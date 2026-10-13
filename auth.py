import hmac
import os
import time
from flask import Blueprint, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash

bp = Blueprint("auth", __name__)
MAX_TENTATIVAS, BLOQUEIO_SEG = 5, 300
falhas = {}  # ip -> (tentativas, expira_em)


def _tentativas(ip):
    n, ate = falhas.get(ip, (0, 0))
    return n if time.time() < ate else 0


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("auth"):
        return redirect("/")
    erro = None
    if request.method == "POST":
        ip = request.remote_addr
        if _tentativas(ip) >= MAX_TENTATIVAS:
            erro = "Muitas tentativas. Aguarde alguns minutos e tente de novo."
        else:
            email = (request.form.get("email") or "").strip().lower().encode()
            senha = request.form.get("senha") or ""
            email_ok = hmac.compare_digest(email, os.environ.get("ADMIN_EMAIL", "").strip().lower().encode())
            hash_ = os.environ.get("ADMIN_PASSWORD_HASH", "")
            senha_ok = bool(hash_) and check_password_hash(hash_, senha)
            if email_ok and senha_ok:
                falhas.pop(ip, None)
                session.clear()
                session["auth"] = True
                session.permanent = True
                return redirect("/")
            falhas[ip] = (_tentativas(ip) + 1, time.time() + BLOQUEIO_SEG)
            erro = "E-mail ou senha incorretos."
    return render_template("login.html", erro=erro), (401 if erro else 200)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


def init_auth(app):
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
        PERMANENT_SESSION_LIFETIME=7 * 24 * 3600,
    )
    app.register_blueprint(bp)

    @app.before_request
    def proteger():
        if request.endpoint in ("auth.login", "static") or session.get("auth"):
            return None
        if request.path.startswith("/api/"):
            return jsonify({"erro": "Sessão expirada. Entre novamente."}), 401
        return redirect("/login")
