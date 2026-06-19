# app/data/empresas_faturadoras_store.py
# Empresas faturadoras: defaults em settings + personalizações na REDE compartilhada.
# Antes ficava em assets/empresas_extra.json dentro do .exe/current — apagado a cada build.

from __future__ import annotations

import copy
import json
import os
import shutil

from app.config.settings import EMPRESAS_FATURADORAS as _EMPRESAS_PADRAO

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOCAL_EMPRESAS_EXTRA_JSON = os.path.join(LOCAL_ASSETS_DIR, "empresas_extra.json")

try:
    from config import BASE_REDE_DIR as REDE_BASE_DIR
except Exception:
    REDE_BASE_DIR = os.path.join(BASE_DIR, "database")

CADASTROS_DIR = os.path.join(REDE_BASE_DIR, "cadastros_compartilhados")
EMPRESAS_EXTRA_JSON = os.path.join(CADASTROS_DIR, "empresas_faturadoras.json")

EMPRESA_PROTEGIDA = "BRASUL"
_META_EXCLUIDAS = "_excluidas"
_EXCLUIDAS_FIXAS = frozenset({"JB"})


def _caminhos_antigos_empresas() -> list[str]:
    """Locais onde personalizações antigas podiam ter sido salvas (antes da rede)."""
    candidatos = [
        LOCAL_EMPRESAS_EXTRA_JSON,
        os.path.join(BASE_DIR, "empresas_extra.json"),
    ]
    # PyInstaller onedir: dados ficavam em _internal/assets (apagado no build)
    interno = os.path.join(BASE_DIR, "assets", "empresas_extra.json")
    if interno not in candidatos:
        candidatos.append(interno)
    # Pasta current ao lado do projeto (atalho na rede)
    try:
        raiz_projeto = os.path.abspath(os.path.join(BASE_DIR, ".."))
        current_interno = os.path.join(
            raiz_projeto, "current", "_internal", "assets", "empresas_extra.json"
        )
        candidatos.append(current_interno)
        candidatos.append(
            os.path.join(raiz_projeto, "current", "assets", "empresas_extra.json")
        )
    except Exception:
        pass
    vistos: set[str] = set()
    unicos: list[str] = []
    for p in candidatos:
        norm = os.path.normpath(p)
        if norm not in vistos:
            vistos.add(norm)
            unicos.append(norm)
    return unicos


def _garantir_armazenamento_empresas() -> None:
    """Garante JSON na rede; migra cópia local antiga se existir."""
    os.makedirs(CADASTROS_DIR, exist_ok=True)
    if os.path.exists(EMPRESAS_EXTRA_JSON):
        return
    for antigo in _caminhos_antigos_empresas():
        if antigo and os.path.isfile(antigo):
            try:
                shutil.copy2(antigo, EMPRESAS_EXTRA_JSON)
                return
            except Exception:
                pass
    # Arquivo criado na primeira edição pelo usuário.


def _carregar_arquivo() -> dict:
    _garantir_armazenamento_empresas()
    if not os.path.exists(EMPRESAS_EXTRA_JSON):
        return {}
    try:
        with open(EMPRESAS_EXTRA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _salvar_arquivo(data: dict) -> None:
    _garantir_armazenamento_empresas()
    os.makedirs(os.path.dirname(EMPRESAS_EXTRA_JSON), exist_ok=True)
    with open(EMPRESAS_EXTRA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _carregar_exclusoes() -> set[str]:
    bruto = _carregar_arquivo().get(_META_EXCLUIDAS, [])
    excl = set(_EXCLUIDAS_FIXAS)
    if isinstance(bruto, list):
        excl.update(str(s).strip() for s in bruto if str(s).strip())
    return excl


def _carregar_extras() -> dict[str, dict]:
    extras = {}
    for sigla, dados in _carregar_arquivo().items():
        if sigla.startswith("_"):
            continue
        if isinstance(dados, dict):
            extras[sigla] = dados
    return extras


def get_empresas_faturadoras() -> dict[str, dict]:
    """Mescla empresas padrão com extras e remove as excluídas pelo usuário."""
    excluidas = _carregar_exclusoes()
    todas = {
        sigla: copy.deepcopy(dados)
        for sigla, dados in _EMPRESAS_PADRAO.items()
        if sigla not in excluidas
    }
    for sigla, dados in _carregar_extras().items():
        if sigla in excluidas:
            continue
        if sigla in todas:
            todas[sigla] = {**todas[sigla], **dados}
        else:
            todas[sigla] = dados
    return todas


def get_empresas_faturadoras_completas() -> dict[str, dict]:
    """Todas as empresas (sem filtro de exclusão) — usado em PDFs de pedidos antigos."""
    todas = copy.deepcopy(_EMPRESAS_PADRAO)
    for sigla, dados in _carregar_extras().items():
        if sigla in todas:
            todas[sigla] = {**todas[sigla], **dados}
        else:
            todas[sigla] = dados
    return todas


def is_empresa_padrao(sigla: str) -> bool:
    return sigla in _EMPRESAS_PADRAO


def is_empresa_apenas_usuario(sigla: str) -> bool:
    return sigla in _carregar_extras() and sigla not in _EMPRESAS_PADRAO


def is_empresa_protegida(sigla: str) -> bool:
    return sigla == EMPRESA_PROTEGIDA


def pode_excluir_empresa(sigla: str) -> bool:
    return bool(sigla) and not is_empresa_protegida(sigla)


def salvar_empresa(sigla: str, dados: dict) -> None:
    arquivo = _carregar_arquivo()
    excluidas = [
        s for s in arquivo.get(_META_EXCLUIDAS, [])
        if str(s).strip() and str(s).strip() != sigla
    ]
    if excluidas:
        arquivo[_META_EXCLUIDAS] = sorted(set(excluidas) | _EXCLUIDAS_FIXAS)
    elif _EXCLUIDAS_FIXAS:
        arquivo[_META_EXCLUIDAS] = sorted(_EXCLUIDAS_FIXAS)
    elif _META_EXCLUIDAS in arquivo:
        del arquivo[_META_EXCLUIDAS]
    arquivo[sigla] = {k: v for k, v in dados.items() if k != "sigla"}
    _salvar_arquivo(arquivo)


def excluir_empresa_faturadora(sigla: str) -> None:
    """Remove empresa do painel. BRASUL não pode ser excluída."""
    if is_empresa_protegida(sigla):
        raise ValueError(f"A empresa {EMPRESA_PROTEGIDA} não pode ser excluída.")

    arquivo = _carregar_arquivo()
    excluidas = set(_carregar_exclusoes())
    excluidas.add(sigla)
    arquivo[_META_EXCLUIDAS] = sorted(excluidas)
    if sigla in arquivo and not sigla.startswith("_"):
        del arquivo[sigla]
    _salvar_arquivo(arquivo)


def restaurar_empresa_padrao(sigla: str) -> None:
    """Remove personalizações e recoloca empresa padrão excluída."""
    if is_empresa_protegida(sigla):
        return
    arquivo = _carregar_arquivo()
    excluidas = [
        s for s in _carregar_exclusoes()
        if s != sigla and s not in _EXCLUIDAS_FIXAS
    ]
    if excluidas:
        arquivo[_META_EXCLUIDAS] = sorted(set(excluidas) | _EXCLUIDAS_FIXAS)
    elif _EXCLUIDAS_FIXAS:
        arquivo[_META_EXCLUIDAS] = sorted(_EXCLUIDAS_FIXAS)
    else:
        arquivo.pop(_META_EXCLUIDAS, None)
    if sigla in arquivo and not sigla.startswith("_"):
        del arquivo[sigla]
    _salvar_arquivo(arquivo)


def remover_empresa(sigla: str) -> None:
    excluir_empresa_faturadora(sigla)


_garantir_armazenamento_empresas()
