"""Gera o arquivo .env com e-mail, senha (só o hash) e chave secreta.
Uso: python criar_acesso.py"""
import getpass
import secrets
from werkzeug.security import generate_password_hash

email = input("E-mail de acesso: ").strip()
senha = getpass.getpass("Senha: ")
if len(senha) < 8:
    raise SystemExit("Use uma senha com pelo menos 8 caracteres.")
h = generate_password_hash(senha, method="pbkdf2:sha256")
with open(".env", "w", encoding="utf-8") as f:
    f.write(f"ADMIN_EMAIL={email}\nADMIN_PASSWORD_HASH='{h}'\nSECRET_KEY={secrets.token_hex(32)}\n")
print(".env criado. Reinicie o servidor.")
