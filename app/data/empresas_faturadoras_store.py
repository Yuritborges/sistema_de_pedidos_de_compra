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

# E-mails do rodapé PDF por empresa (padrão oficial)
_RODAPE_PADRAO: dict[str, dict[str, str]] = {
    "BRASUL": {
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "",
    },
    "B&B": {
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "",
    },
    "INTERIORANA": {
        "email_rodape_1": "notafiscal@construtorainteriorana.com",
        "email_rodape_2": "",
    },
    "INTERBRAS": {
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "",
    },
}


def _corrigir_emails_rodape_empresa(sigla: str, dados: dict) -> dict:
    """Garante e-mails de rodapé corretos (evita .com.br antigo da Interiorana)."""
    if not isinstance(dados, dict):
        return dados
    padrao = _RODAPE_PADRAO.get(sigla)
    if not padrao:
        return dados
    for chave, correto in padrao.items():
        if chave == "email_rodape_1":
            dados[chave] = correto
        elif chave == "email_rodape_2":
            dados[chave] = correto
    return dados


def _aplicar_correcoes_pos_merge(todas: dict[str, dict]) -> dict[str, dict]:
    for sigla, dados in todas.items():
        _corrigir_emails_rodape_empresa(sigla, dados)
    return todas


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


def _garantir_emails_rodape_no_arquivo() -> None:
    """Persiste e-mails de rodapé corretos na rede (vale mesmo com .exe antigo)."""
    if not os.path.exists(EMPRESAS_EXTRA_JSON):
        return
    try:
        with open(EMPRESAS_EXTRA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return
        alterou = False
        for sigla in _RODAPE_PADRAO:
            bloco = data.get(sigla)
            if not isinstance(bloco, dict):
                continue
            antes = json.dumps(bloco, sort_keys=True)
            _corrigir_emails_rodape_empresa(sigla, bloco)
            if json.dumps(bloco, sort_keys=True) != antes:
                data[sigla] = bloco
                alterou = True
        if alterou:
            _salvar_arquivo(data)
    except Exception:
        pass


def _garantir_armazenamento_empresas() -> None:
    """Garante JSON na rede; migra cópia local antiga se existir."""
    os.makedirs(CADASTROS_DIR, exist_ok=True)
    if os.path.exists(EMPRESAS_EXTRA_JSON):
        _garantir_emails_rodape_no_arquivo()
        return
    for antigo in _caminhos_antigos_empresas():
        if antigo and os.path.isfile(antigo):
            try:
                shutil.copy2(antigo, EMPRESAS_EXTRA_JSON)
                _garantir_emails_rodape_no_arquivo()
                return
            except Exception:
                pass
    # Arquivo criado na primeira edição ou pelo seed abaixo.


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
    return _aplicar_correcoes_pos_merge(todas)


def get_empresas_faturadoras_completas() -> dict[str, dict]:
    """Todas as empresas (sem filtro de exclusão) — usado em PDFs de pedidos antigos."""
    todas = copy.deepcopy(_EMPRESAS_PADRAO)
    for sigla, dados in _carregar_extras().items():
        if sigla in todas:
            todas[sigla] = {**todas[sigla], **dados}
        else:
            todas[sigla] = dados
    return _aplicar_correcoes_pos_merge(todas)


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
    novos = {k: v for k, v in dados.items() if k != "sigla"}
    existente = arquivo.get(sigla, {})
    if isinstance(existente, dict):
        merged = {**existente, **novos}
    else:
        merged = novos
    if sigla in _RODAPE_PADRAO:
        _corrigir_emails_rodape_empresa(sigla, merged)
    arquivo[sigla] = merged
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


def _seed_emails_rodape_rede() -> None:
    """
    Grava e-mails oficiais de rodapé na rede para todas as empresas padrão.
    Sobrescreve defaults embutidos no .exe (inclusive e-mails antigos/errados).
    """
    os.makedirs(CADASTROS_DIR, exist_ok=True)
    data: dict = {}
    if os.path.exists(EMPRESAS_EXTRA_JSON):
        try:
            with open(EMPRESAS_EXTRA_JSON, "r", encoding="utf-8") as f:
                carregado = json.load(f)
            if isinstance(carregado, dict):
                data = carregado
        except Exception:
            data = {}
    for sigla, emails in _RODAPE_PADRAO.items():
        bloco = data.get(sigla)
        if not isinstance(bloco, dict):
            bloco = {}
        bloco.update(emails)
        data[sigla] = bloco
    if _EXCLUIDAS_FIXAS:
        data[_META_EXCLUIDAS] = sorted(
            set(data.get(_META_EXCLUIDAS, [])) | _EXCLUIDAS_FIXAS
        )
    _salvar_arquivo(data)


_garantir_armazenamento_empresas()
_seed_emails_rodape_rede()
