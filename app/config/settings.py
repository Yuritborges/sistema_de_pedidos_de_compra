# app/config/settings.py
# Configurações centralizadas compartilhadas por todas as instalações.
# Caminhos de rede e usuário ativo continuam em config.py (raiz do projeto).

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Metadados do aplicativo
# ---------------------------------------------------------------------------
APP_NAME = "Sistema de Pedidos — Brasul"
APP_VERSION = "2.1.3"
ORGANIZATION_NAME = "Brasul Construtora"

def env_bool(name: str, default: bool) -> bool:
    """
    Lê variável de ambiente como booleano.
    Aceita: 1/true/yes/sim e 0/false/no/nao/não.
    """
    valor = (os.environ.get(name) or "").strip().lower()
    if valor in ("1", "true", "yes", "sim"):
        return True
    if valor in ("0", "false", "no", "nao", "não"):
        return False
    return default


def is_debug_mode() -> bool:
    """Indica se o modo debug está ativo."""
    return env_bool("BRASUL_DEBUG", False)


# ---------------------------------------------------------------------------
# Modo debug (logs extras de SQL, startup, etc.)
# ---------------------------------------------------------------------------
DEBUG = is_debug_mode()

# ---------------------------------------------------------------------------
# Tema visual (preparado para centralização na Fase 2 — ui/styles/theme.py)
# Paleta atual do sistema Brasul (vermelho corporativo).
# ---------------------------------------------------------------------------
THEME: dict[str, Any] = {
    "mode": "light",
    "font_family": "Segoe UI",
    "font_family_fallback": "Arial",
    "colors": {
        "primary": "#C0392B",
        "primary_dark": "#B91C1C",
        "background": "#F0EDED",
        "surface": "#FFFFFF",
        "text": "#111827",
        "text_secondary": "#6B7280",
        "border": "#E5E7EB",
        "success": "#1E8449",
        "danger": "#C0392B",
        "info": "#2980B9",
        "sidebar_bg": "#F0EDED",
        "sidebar_active": "#FDECEA",
    },
}

# ---------------------------------------------------------------------------
# Rede — valores padrão (config.py pode sobrescrever por máquina)
# ---------------------------------------------------------------------------
DEFAULT_BASE_REDE_SUFFIX = os.path.join("0 OBRAS", "brasul_pedidos")
# Mapeamento novo (2026-07): unidade pode apontar direto para "0 obras",
# ficando a pasta em {letra}:\brasul_pedidos.
DEFAULT_BASE_REDE_NOME = "brasul_pedidos"
# Fallback no layout NOVO — nunca recriar a estrutura antiga em 0 OBRAS.
DEFAULT_BASE_REDE_DIR = r"Z:\brasul_pedidos"
DEFAULT_BASE_REDE_UNC = r"\\192.168.15.250\arquivos brasul\0 obras\brasul_pedidos"
DEFAULT_PASTA_FERRAMENTAS_NOME = "FERRAMENTAS"
# Layout antigo (pre-remap): {letra}:\0 OBRAS\FERRAMENTAS
DEFAULT_PASTA_FERRAMENTAS_SUFFIX = os.path.join("0 OBRAS", "FERRAMENTAS")
# Layout novo (2026-07): unidade aponta para "0 obras" -> {letra}:\FERRAMENTAS
DEFAULT_PASTA_FERRAMENTAS_DIR = r"Z:\FERRAMENTAS"
DEFAULT_PASTA_FERRAMENTAS_UNC = r"\\192.168.15.250\arquivos brasul\0 obras\FERRAMENTAS"
DEFAULT_REDE_SYNC_INTERVALO_SEGUNDOS = 300
DEFAULT_BACKUP_REDE_INTERVALO_SEGUNDOS = 900
DEFAULT_REDE_SYNC_CONSOLIDAR_COMPLETO = True
DEFAULT_REDE_SYNC_MESCLAR_CONSOLIDADO = False
# Servidor de arquivos (Intranet Windows — evita aviso ao abrir atalhos na rede)
DEFAULT_SERVIDOR_REDE_HOST = "192.168.15.250"
DEFAULT_CONFIGURAR_INTRANET_WINDOWS = True

# ---------------------------------------------------------------------------
# Empresas faturadoras (dados dos PDFs de pedido)
# email_rodape_1 / email_rodape_2: rodapé "Notas e Boletos encaminha para:"
# ---------------------------------------------------------------------------
EMPRESAS_FATURADORAS: dict[str, dict[str, Any]] = {
    "BRASUL": {
        "razao_social": "BRASUL CONSTRUTORA LTDA",
        "cnpj": "72.767.239/0001-00",
        "endereco": "Rua Coronel Jordão, 440, Vila Paiva - São Paulo, SP - CEP 02075-030",
        "telefone": "(11) 3313-8220",
        "email": "compras2@brasulconstrutora.com.br",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "",
        "logo": "logo_brasul.png",
        "obs_padrao": (
            "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\n"
            "BRASUL CONSTRUTORA LTDA"
        ),
        "cor_header": (0, 51, 102),
    },
    "B&B": {
        "razao_social": "B & B Engenharia e Construções LTDA",
        "cnpj": "03.643.992/0001-63",
        "endereco": "Rua Itamonte 33, Vila Medeiros - São Paulo, SP - CEP 02220-000",
        "telefone": "(11) 3313-8220",
        "email": "compras2@brasulconstrutora.com.br",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "",
        "logo": "logo_bb.png",
        "obs_padrao": (
            "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\n"
            "B&B Engenharia e Construções LTDA"
        ),
        "cor_header": (0, 100, 0),
    },
    "INTERIORANA": {
        "razao_social": "CONSTRUTORA INTERIORANA LTDA",
        "cnpj": "10.471.329/0001-94",
        "endereco": (
            "Rua Cel Jordão, 458 Fundos Sala 2 – Vila Paiva – "
            "São Paulo, SP - CEP 02075-030"
        ),
        "cidade": "São Paulo",
        "uf": "SP",
        "cep": "02075-030",
        "telefone": "(11) 3641-9169",
        "email": "compra2@construtorainteriorana.com",
        "email_rodape_1": "notafiscal@construtorainteriorana.com",
        "email_rodape_2": "",
        "logo": "logo_interiorana.png",
        "obs_padrao": (
            "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\n"
            "CONSTRUTORA INTERIORANA LTDA"
        ),
        "cor_header": (100, 50, 0),
    },
    "INTERBRAS": {
        "razao_social": "CONSÓRCIO INTERBRAS",
        "cnpj": "65.886.971/0001-26",
        "endereco": "Rua Coronel Jordão, 440, Vila Paiva - São Paulo, SP - CEP 02075-030",
        "telefone": "(11) 3313-8220",
        "email": "",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "",
        "logo": "logo_interbras.png",
        "obs_padrao": (
            "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\n"
            "INTERBRAS CONSTRUTORA LTDA"
        ),
        "cor_header": (50, 50, 130),
    },
}

# ---------------------------------------------------------------------------
# Constantes de negócio (formulários, itens, pagamento)
# ---------------------------------------------------------------------------
CATEGORIAS_ITEM = [
    "FUNDAÇÃO / ESTRUTURA",
    "COBERTURA / FORRO",
    "HIDRAULICA",
    "ELETRICA",
    "REVESTIMENTO / PISO",
    "VIDRO / CAIXILHARIA",
    "PINTURA",
    "INCENDIO",
    "LOCAÇÃO",
    "OUTROS",
]

UNIDADES = [
    "UNID.", "M", "M2", "M3", "KG", "SACO", "ROLO",
    "PACOTE", "BARRICA", "BALDE", "LATA", "GALÃO",
    "BARRA", "PEÇA", "JOGO", "CONJ.", "VERBA",
]

CONDICOES_PAGAMENTO = [
    "7", "14", "21", "28", "30",
    "28/35/42", "30/45/60", "30/60/90",
    "28/42", "30/60", "À VISTA",
]

FORMAS_PAGAMENTO = ["BOLETO", "PIX", "CARTÃO"]


# ---------------------------------------------------------------------------
# Helpers — usuário e caminhos na rede
# ---------------------------------------------------------------------------
def normalizar_usuario(nome: str) -> str:
    """Normaliza nome do comprador (YURI → IURY, maiúsculas)."""
    nome = (nome or "").strip().upper()
    if not nome:
        return "IURY"
    if nome == "YURI":
        return "IURY"
    return nome


def slug_usuario(nome: str) -> str:
    """Slug alfanumérico para nome de arquivo .db (ex.: IURY → iury)."""
    slug = "".join(ch.lower() for ch in normalizar_usuario(nome) if ch.isalnum())
    return slug or "usuario"


def _pasta_rede_brasul_valida(caminho: str) -> bool:
    """True se a pasta parece ser a raiz brasul_pedidos na rede."""
    if not caminho or not os.path.isdir(caminho):
        return False
    marcadores = (
        os.path.join(caminho, "cotacao_rede.db"),
        os.path.join(caminho, "cadastros_compartilhados"),
        os.path.join(caminho, "Iury"),
        os.path.join(caminho, "Thamyres"),
    )
    return any(os.path.exists(m) for m in marcadores)


def _pasta_rede_com_dados_reais(caminho: str) -> bool:
    """True se a pasta contém dados de produção (não apenas estrutura recriada).

    Programas antigos recriavam a árvore vazia em {letra}:\\0 OBRAS\\brasul_pedidos
    quando não achavam a rede — essa cópia "fantasma" não pode ser escolhida.
    """
    if not _pasta_rede_brasul_valida(caminho):
        return False
    pontos = 0
    if os.path.isfile(os.path.join(caminho, "cotacao_rede.db")):
        pontos += 1
    obras_json = os.path.join(caminho, "cadastros_compartilhados", "obras.json")
    fornecedores_json = os.path.join(caminho, "cadastros_compartilhados", "fornecedores.json")
    for arq in (obras_json, fornecedores_json):
        try:
            if os.path.getsize(arq) > 1024:
                pontos += 1
        except OSError:
            pass
    usuarios = 0
    for pasta in ("Iury", "Thamyres", "SuaPasta", "CI"):
        if os.path.isdir(os.path.join(caminho, pasta)):
            usuarios += 1
    if usuarios >= 2:
        pontos += 1
    return pontos >= 2


def _candidatos_base_rede() -> list[str]:
    """Candidatos em ordem de prioridade: layout novo antes do antigo."""
    env = (os.environ.get("BRASUL_REDE_DIR") or "").strip()
    candidatos: list[str] = []
    if env:
        candidatos.append(env)
    # Layout novo primeiro: unidade aponta direto para a pasta "0 obras"
    for letra in "ZYXWVUTSRQPONMLKJIHGFED":
        candidatos.append(os.path.join(f"{letra}:\\", DEFAULT_BASE_REDE_NOME))
    candidatos.append(DEFAULT_BASE_REDE_UNC)
    # Layout antigo por último (pode existir uma cópia vazia recriada por engano)
    for letra in "ZYXWVUTSRQPONMLKJIHGFED":
        candidatos.append(os.path.join(f"{letra}:\\", DEFAULT_BASE_REDE_SUFFIX))
    candidatos.append(DEFAULT_BASE_REDE_DIR)
    return candidatos


def resolver_base_rede_dir() -> str:
    """
    Descobre a pasta brasul_pedidos na rede.

    Ordem: variável BRASUL_REDE_DIR → layout novo ({letra}:\\brasul_pedidos) →
    UNC → layout antigo ({letra}:\\0 OBRAS\\brasul_pedidos) → DEFAULT_BASE_REDE_DIR.
    Passa 1 exige dados reais (bancos/cadastros preenchidos); passa 2 aceita
    qualquer pasta com a estrutura, para não quebrar instalações novas.
    """
    candidatos = _candidatos_base_rede()

    for validador in (_pasta_rede_com_dados_reais, _pasta_rede_brasul_valida):
        vistos: set[str] = set()
        for bruto in candidatos:
            caminho = os.path.normpath(bruto)
            chave = caminho.lower()
            if chave in vistos:
                continue
            vistos.add(chave)
            if validador(caminho):
                return caminho
    return DEFAULT_BASE_REDE_DIR




def _candidatos_pasta_ferramentas() -> list[str]:
    """Candidatos da pasta de fotos FERRAMENTAS: layout novo antes do antigo."""
    env = (os.environ.get("BRASUL_FERRAMENTAS_DIR") or "").strip()
    candidatos: list[str] = []
    if env:
        candidatos.append(env)
    for letra in "ZYXWVUTSRQPONMLKJIHGFED":
        candidatos.append(os.path.join(f"{letra}:\\", DEFAULT_PASTA_FERRAMENTAS_NOME))
    candidatos.append(DEFAULT_PASTA_FERRAMENTAS_UNC)
    for letra in "ZYXWVUTSRQPONMLKJIHGFED":
        candidatos.append(os.path.join(f"{letra}:\\", DEFAULT_PASTA_FERRAMENTAS_SUFFIX))
    candidatos.append(DEFAULT_PASTA_FERRAMENTAS_DIR)
    return candidatos


def resolver_pasta_ferramentas() -> str:
    """
    Descobre a pasta FERRAMENTAS na rede (fotos dos equipamentos).

    Ordem: BRASUL_FERRAMENTAS_DIR -> layout novo ({letra}:\FERRAMENTAS) ->
    UNC -> layout antigo ({letra}:\0 OBRAS\FERRAMENTAS) -> DEFAULT_PASTA_FERRAMENTAS_DIR.
    """
    vistos: set[str] = set()
    for bruto in _candidatos_pasta_ferramentas():
        caminho = os.path.normpath(bruto)
        chave = caminho.lower()
        if chave in vistos:
            continue
        vistos.add(chave)
        if os.path.isdir(caminho):
            return caminho
    return DEFAULT_PASTA_FERRAMENTAS_DIR

def caminhos_comprador(base_rede_dir: str, comprador: str) -> dict[str, str]:
    """
    Monta caminhos de banco, PDFs, cotações e backup para um comprador.

    Returns:
        dict com DATABASE_PATH, PEDIDOS_DIR, COTACOES_DIR, BACKUP_DIR, RELACOES_DIR.
    """
    pasta = normalizar_usuario(comprador).title()
    slug = slug_usuario(comprador)
    raiz = os.path.join(base_rede_dir, pasta)
    return {
        "DATABASE_PATH": os.path.join(raiz, f"cotacao_{slug}.db"),
        "PEDIDOS_DIR": os.path.join(raiz, "pdfs de pedidos"),
        "COTACOES_DIR": os.path.join(raiz, "cotações_salvas"),
        "BACKUP_DIR": os.path.join(raiz, "backup"),
        "RELACOES_DIR": os.path.join(raiz, "relações"),
    }


def configurar_locacoes(pkg_root: str) -> dict[str, Any]:
    """
    Configuração de importação automática da planilha de locações.

    Args:
        pkg_root: pasta raiz do projeto (onde fica config.py).

    Returns:
        dict com LOCACOES_PLANILHA_ENV, LOCACOES_PLANILHA_MANUAL,
        LOCACOES_PLANILHA_CANDIDATES, LOCACOES_AUTO_IMPORT_SE_VAZIO,
        LOCACOES_AUTO_SYNC_PLANILHA_NOVA.
    """
    return {
        "LOCACOES_PLANILHA_ENV": (os.environ.get("BRASUL_LOCACOES_XLSM") or "").strip(),
        "LOCACOES_PLANILHA_MANUAL": "",
        "LOCACOES_PLANILHA_CANDIDATES": [
            os.path.join(pkg_root, "LOCAÇÕES - LANÇAMENTO.xlsm"),
            os.path.join(pkg_root, "LOCAÇOES - LANÇAMENTO.xlsm"),
        ],
        "LOCACOES_AUTO_IMPORT_SE_VAZIO": env_bool("BRASUL_LOCACOES_AUTO", True),
        "LOCACOES_AUTO_SYNC_PLANILHA_NOVA": env_bool("BRASUL_LOCACOES_SYNC_MTIME", False),
    }


# ---------------------------------------------------------------------------
# Google Drive — Backup em Nuvem (backup_agendado.py)
# token.json e credenciais OAuth NÃO devem ir para o Git.
# ---------------------------------------------------------------------------
_CONFIG_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CONFIG_DIR.parent.parent

CREDENTIALS_DRIVE_PATH: str = str(_CONFIG_DIR / "brasul-drive-credentials.json")
TOKEN_DRIVE_PATH: str = str(_CONFIG_DIR / "token.json")
DRIVE_BACKUP_FOLDER_NAME: str = "Brasul_Backups"
# ID da pasta no Drive (trecho final da URL da pasta Brasul_Backups)
DRIVE_FOLDER_ID: str = "15o-YjEScb-IxtsgBNd6_ODAqi1NPvm0T"

# Banco consolidado enviado ao Drive (auditoria / backup principal)
def _drive_paths_rede() -> tuple[str, str]:
    base = resolver_base_rede_dir()
    return (
        os.path.join(base, "cotacao_rede.db"),
        os.path.join(base, "BACKUPS"),
    )


_DRIVE_BANCO, _DRIVE_BACKUP = _drive_paths_rede()
DRIVE_BANCO_ORIGEM: str = _DRIVE_BANCO
DRIVE_PASTA_BACKUP_LOCAL: str = _DRIVE_BACKUP
DRIVE_BACKUP_LOG_PATH: str = str(_PROJECT_ROOT / "backup_agendado.log")

# ---------------------------------------------------------------------------
# PDF — observação padrão (bloco NOTA FISCAL em todos os pedidos)
# ---------------------------------------------------------------------------
OBS_FATURAMENTO_DATA_ENTREGA: str = (
    "A NOTA FISCAL E O BOLETO BANCÁRIO DEVERÃO SER EMITIDOS EXCLUSIVAMENTE NA "
    "DATA DA ENTREGA EFETIVA DO MATERIAL NA OBRA, SENDO EXPRESSAMENTE VEDADA A "
    "EMISSÃO ANTECIPADA NA DATA DO PEDIDO OU ANTES DA ENTREGA. O PRAZO DE "
    "PAGAMENTO SERÁ CONTADO A PARTIR DA DATA REAL DA ENTREGA DO MATERIAL."
)
