# app/data/usuarios_store.py
# Usuários do login e e-mail exibido no cabeçalho dos PDFs de pedido.

from __future__ import annotations

import json
import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
USUARIOS_JSON = os.path.join(BASE_DIR, "assets", "usuarios.json")

USUARIOS_PADRAO = ("IURY", "THAMYRES")

# E-mails padrão dos compradores Interiorana (podem ser sobrescritos em usuarios.json).
EMAILS_PADRAO = {
    "IURY": "compra2@construtorainteriorana.com",
    "THAMYRES": "compra1@construtorainteriorana.com",
}


def _normalizar_nome(nome: str) -> str:
    return str(nome or "").strip().upper()


def _caminho_usuarios() -> str:
    return USUARIOS_JSON


def _carregar_dados() -> dict:
    dados = {"usuarios": [], "emails": {}}
    caminho = _caminho_usuarios()
    if not os.path.exists(caminho):
        return dados
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            bruto = json.load(f)
    except Exception:
        return dados
    if not isinstance(bruto, dict):
        return dados

    extras = bruto.get("usuarios") or []
    if isinstance(extras, list):
        dados["usuarios"] = [
            _normalizar_nome(u) for u in extras if _normalizar_nome(u)
        ]

    emails = bruto.get("emails") or {}
    if isinstance(emails, dict):
        for chave, valor in emails.items():
            nome = _normalizar_nome(chave)
            email = str(valor or "").strip()
            if nome and email:
                dados["emails"][nome] = email
    return dados


def _salvar_dados(dados: dict) -> None:
    caminho = _caminho_usuarios()
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    extras = [
        u for u in dados.get("usuarios", [])
        if u not in USUARIOS_PADRAO
    ]
    payload = {
        "usuarios": extras,
        "emails": dict(dados.get("emails") or {}),
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def listar_usuarios() -> list[str]:
    dados = _carregar_dados()
    usuarios = list(USUARIOS_PADRAO)
    for nome in dados["usuarios"]:
        if nome not in usuarios:
            usuarios.append(nome)
    return usuarios


def obter_email_comprador(nome: str) -> str:
    """E-mail do comprador para o cabeçalho do PDF."""
    nome = _normalizar_nome(nome)
    if not nome:
        return ""
    dados = _carregar_dados()
    if nome in dados["emails"]:
        return dados["emails"][nome]
    return EMAILS_PADRAO.get(nome, "")


def salvar_email_comprador(nome: str, email: str) -> None:
    nome = _normalizar_nome(nome)
    email = str(email or "").strip()
    if not nome:
        raise ValueError("Nome de usuário inválido.")
    if not email:
        raise ValueError("Informe o e-mail do usuário.")
    if not email_valido(email):
        raise ValueError("E-mail inválido.")
    dados = _carregar_dados()
    dados["emails"][nome] = email
    _salvar_dados(dados)


def registrar_usuario_extra(nome: str, email: str) -> None:
    """Cadastra usuário adicional e o e-mail dele."""
    nome = _normalizar_nome(nome)
    email = str(email or "").strip()
    if not nome:
        raise ValueError("Informe um nome de usuário.")
    if not email:
        raise ValueError("Informe o e-mail do usuário.")
    if not email_valido(email):
        raise ValueError("E-mail inválido.")

    dados = _carregar_dados()
    if nome not in USUARIOS_PADRAO and nome not in dados["usuarios"]:
        dados["usuarios"].append(nome)
    dados["emails"][nome] = email
    _salvar_dados(dados)


def email_valido(email: str) -> bool:
    email = str(email or "").strip()
    if not email or " " in email:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def garantir_emails_padrao_no_arquivo() -> None:
    """Grava e-mails padrão de Iury/Thamyres se o arquivo ainda não existir."""
    caminho = _caminho_usuarios()
    if os.path.exists(caminho):
        return
    dados = {"usuarios": [], "emails": dict(EMAILS_PADRAO)}
    _salvar_dados(dados)
