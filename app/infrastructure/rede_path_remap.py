# app/infrastructure/rede_path_remap.py
"""Remapeia caminhos gravados no layout antigo da rede para o mapeamento novo."""
from __future__ import annotations

import os
import re

from app.config.settings import DEFAULT_SERVIDOR_REDE_HOST

_UNC_ARQUIVOS = rf"\\{DEFAULT_SERVIDOR_REDE_HOST}\arquivos brasul"
_RE_DRIVE_OBRAS = re.compile(r"^([a-zA-Z]):\\0 obras\\(.+)$", re.IGNORECASE)


def candidatos_caminho_rede(caminho: str) -> list[str]:
    """
    Gera caminhos equivalentes apos o remap do Z: (jul/2026).

    Antigo: unidade -> \\\\server\\arquivos brasul\\ -> Z:\\0 OBRAS\\...
    Novo:   unidade -> \\\\server\\arquivos brasul\\0 obras\\ -> Z:\\...
    """
    txt = str(caminho or "").strip()
    if not txt:
        return []

    out: list[str] = []
    seen: set[str] = set()

    def _add(*paths: str) -> None:
        for p in paths:
            if not p:
                continue
            norm = os.path.normpath(p)
            key = norm.lower()
            if key not in seen:
                seen.add(key)
                out.append(norm)

    _add(txt)
    slash = os.path.normpath(txt).replace("/", "\\")

    m = _RE_DRIVE_OBRAS.match(slash)
    if m:
        _add(f"{m.group(1).upper()}:\\{m.group(2)}")

    low = slash.lower()
    for marc in (
        f"{_UNC_ARQUIVOS}\\0 obras\\",
        f"{_UNC_ARQUIVOS}\\0 OBRAS\\",
    ):
        idx = low.find(marc.lower())
        if idx >= 0:
            resto = slash[idx + len(marc):]
            if resto:
                _add(f"{_UNC_ARQUIVOS}\\0 obras\\{resto}")
            break

    if "\\0 obras\\" in low and not m:
        idx = low.find("\\0 obras\\")
        stripped = slash[:idx] + "\\" + slash[idx + len("\\0 obras\\"):]
        _add(stripped)

    return out


def _pasta_pdfs_atual() -> str:
    try:
        from config import PEDIDOS_DIR

        return PEDIDOS_DIR
    except Exception:
        from app.config.settings import caminhos_comprador, normalizar_usuario, resolver_base_rede_dir

        comprador = (os.environ.get("BRASUL_USUARIO") or "IURY").strip()
        return caminhos_comprador(resolver_base_rede_dir(), normalizar_usuario(comprador))[
            "PEDIDOS_DIR"
        ]


def resolver_caminho_arquivo_rede(caminho: str, numero_pedido: str = "") -> str:
    """
    Retorna o primeiro caminho de arquivo existente (original ou remapeado).
    Com numero_pedido, tenta achar PC-{numero}.pdf na pasta de PDFs atual.
    """
    for cand in candidatos_caminho_rede(caminho):
        if os.path.isfile(cand):
            return cand

    num = str(numero_pedido or "").strip()
    if num:
        pasta = _pasta_pdfs_atual()
        for nome in (f"PC-{num}.pdf", f"PC-{num.upper()}.pdf"):
            p = os.path.join(pasta, nome)
            if os.path.isfile(p):
                return p
        if os.path.isdir(pasta):
            alvo = num.upper()
            try:
                with os.scandir(pasta) as it:
                    for entry in it:
                        if not entry.is_file() or not entry.name.lower().endswith(".pdf"):
                            continue
                        nu = entry.name.upper()
                        if nu.startswith(f"PC-{alvo}-") or nu == f"PC-{alvo}.PDF":
                            return entry.path
            except OSError:
                pass

    cands = candidatos_caminho_rede(caminho)
    return cands[0] if cands else str(caminho or "")


def resolver_caminho_existente_rede(caminho: str) -> str:
    """Como resolver_caminho_arquivo_rede, sem fallback por numero de pedido."""
    return resolver_caminho_arquivo_rede(caminho, "")
