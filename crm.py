import os
import sqlite3
from datetime import datetime
from flask import Blueprint, g, jsonify, request

bp = Blueprint("crm", __name__)
DB = os.environ.get("DB_PATH", "painel.db")
CAMPOS = {"nome", "telefone", "endereco", "whatsapp", "ramo", "status", "valor", "followup", "notas"}


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@bp.teardown_app_request
def fechar(_):
    d = g.pop("db", None)
    if d:
        d.close()


def agora():
    return datetime.now().isoformat(timespec="minutes")


def init_db():
    os.makedirs(os.path.dirname(DB) or ".", exist_ok=True)
    with sqlite3.connect(DB) as c:
        c.executescript("""
        create table if not exists leads(id integer primary key, nome text, telefone text, endereco text,
          whatsapp text, ramo text, status text default 'novo', valor real default 0, followup text,
          notas text default '[]', criado text, contactado_em text);
        create table if not exists templates(id integer primary key, canal text, titulo text, corpo text);
        """)
        if not c.execute("select 1 from templates").fetchone():
            c.executemany("insert into templates(canal,titulo,corpo) values(?,?,?)", [
                ("whatsapp", "Primeira abordagem",
                 "Olá! Vi que a {{nome_empresa}} ainda não tem site. Trabalho com sites para {{ramo_atividade}} "
                 "e posso mostrar como isso traria mais clientes. Posso te enviar uma proposta?"),
                ("email", "Apresentação por e-mail",
                 "Olá, equipe da {{nome_empresa}}! Notei que vocês não têm site e quero mostrar como "
                 "um site pode atrair mais clientes para {{ramo_atividade}}."),
            ])


@bp.get("/api/leads")
def listar():
    return jsonify([dict(r) for r in db().execute("select * from leads order by id desc")])


@bp.post("/api/leads")
def criar():
    d = request.get_json() or {}
    if db().execute("select 1 from leads where nome=? and telefone=?", (d.get("nome"), d.get("telefone"))).fetchone():
        return jsonify({"erro": "Essa empresa já está no CRM"}), 409
    st = d.get("status", "novo")
    cur = db().execute(
        "insert into leads(nome,telefone,endereco,whatsapp,ramo,status,criado,contactado_em) values(?,?,?,?,?,?,?,?)",
        (d.get("nome"), d.get("telefone"), d.get("endereco"), d.get("whatsapp"), d.get("ramo"), st,
         agora(), agora() if st != "novo" else None))
    db().commit()
    return jsonify({"id": cur.lastrowid}), 201


@bp.patch("/api/leads/<int:i>")
def atualizar(i):
    d = {k: v for k, v in (request.get_json() or {}).items() if k in CAMPOS}
    if not d:
        return jsonify({"erro": "Nada para atualizar"}), 400
    sets, extra, args = ", ".join(f"{k}=?" for k in d), "", list(d.values())
    if d.get("status", "novo") != "novo":
        extra = ", contactado_em=coalesce(contactado_em, ?)"
        args.append(agora())
    db().execute(f"update leads set {sets}{extra} where id=?", args + [i])
    db().commit()
    return jsonify({"ok": True})


@bp.delete("/api/leads/<int:i>")
def apagar(i):
    db().execute("delete from leads where id=?", (i,))
    db().commit()
    return jsonify({"ok": True})


@bp.get("/api/templates")
def listar_templates():
    return jsonify([dict(r) for r in db().execute("select * from templates order by id")])


@bp.post("/api/templates")
def criar_template():
    d = request.get_json() or {}
    db().execute("insert into templates(canal,titulo,corpo) values(?,?,?)", (d.get("canal"), d.get("titulo"), d.get("corpo")))
    db().commit()
    return jsonify({"ok": True}), 201


@bp.delete("/api/templates/<int:i>")
def apagar_template(i):
    db().execute("delete from templates where id=?", (i,))
    db().commit()
    return jsonify({"ok": True})
