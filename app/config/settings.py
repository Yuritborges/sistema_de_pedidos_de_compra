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
APP_VERSION = "2.1.2"
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
DEFAULT_BASE_REDE_DIR = r"Z:\0 OBRAS\brasul_pedidos"
DEFAULT_REDE_SYNC_INTERVALO_SEGUNDOS = 300
DEFAULT_BACKUP_REDE_INTERVALO_SEGUNDOS = 900
DEFAULT_REDE_SYNC_CONSOLIDAR_COMPLETO = True
DEFAULT_REDE_SYNC_MESCLAR_CONSOLIDADO = False

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
        "email_rodape_2": "viviane@brasulconstrutora.com.br",
        "logo": "logo_brasul.png",
        "obs_padrao": (
            "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\n"
            "BRASUL CONSTRUTORA LTDA"
        ),
        "cor_header": (0, 51, 102),
    },
    "JB": {
        "razao_social": "JB CONSTRUÇÕES E EMPREENDIMENTOS LTDA",
        "endereco": "Av Luis Dummount Vilares 2078, São Paulo, SP - CEP 02239-000",
        "telefone": "(11) 3313-8220",
        "email": "compras2@brasulconstrutora.com.br",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "viviane@brasulconstrutora.com.br",
        "logo": "logo_jb.png",
        "obs_padrao": (
            "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\n"
            "JB CONSTRUÇÕES E EMPREENDIMENTOS LTDA"
        ),
        "cor_header": (180, 0, 0),
    },
    "B&B": {
        "razao_social": "B & B Engenharia e Construções LTDA",
        "cnpj": "03.643.992/0001-63",
        "endereco": "Rua Itamonte 33, Vila Medeiros - São Paulo, SP - CEP 02220-000",
        "telefone": "(11) 3313-8220",
        "email": "compras2@brasulconstrutora.com.br",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "viviane@brasulconstrutora.com.br",
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
            "Av. Independência, 546 sala 93 – Cidade Alta – "
            "Piracicaba, SP - CEP 13419-160"
        ),
        "telefone": "(11) 3641-9169",
        "email": "compra2@construtorainteriorana.com",
        "email_rodape_1": "notafiscal@construtorainteriorana.com.br",
        "email_rodape_2": "financeiro2@construtorainteriorana.com.br",
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
        "email_rodape_2": "viviane@brasulconstrutora.com.br",
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


# ---------------------------------------------------------------------------  ← NOVO
# Google Drive — Backup em Nuvem
# O arquivo JSON de credenciais NÃO deve ser commitado no Git.
# Adicione ao .gitignore: app/config/*.json
# ---------------------------------------------------------------------------
# Raiz do pacote (pasta app/config/ → sobe um nível → app/)
_CONFIG_DIR = Path(__file__).resolve().parent

# Caminho esperado: app/config/brasul-drive-credentials.json
CREDENTIALS_DRIVE_PATH: str = str(_CONFIG_DIR / "brasul-drive-credentials.json")

# Nome da pasta raiz criada no Google Drive
DRIVE_BACKUP_FOLDER_NAME: str = "Brasul_Backups"
