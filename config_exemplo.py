# config_exemplo.py — modelo para gerar config.py (não use este nome em produção).
# Copie para config.py e ajuste COMPRADOR_PADRAO / BASE_REDE_DIR se necessário.
# Constantes compartilhadas (empresas, categorias, unidades) vêm de app.config.settings.

import os

from app.config.settings import (
    CATEGORIAS_ITEM,
    CONDICOES_PAGAMENTO,
    DEFAULT_BACKUP_REDE_INTERVALO_SEGUNDOS,
    DEFAULT_BASE_REDE_DIR,
    DEFAULT_REDE_SYNC_CONSOLIDAR_COMPLETO,
    DEFAULT_REDE_SYNC_INTERVALO_SEGUNDOS,
    DEFAULT_REDE_SYNC_MESCLAR_CONSOLIDADO,
    EMPRESAS_FATURADORAS,
    FORMAS_PAGAMENTO,
    UNIDADES,
    caminhos_comprador,
    configurar_locacoes,
    env_bool,
    normalizar_usuario,
)

# ---------------------------------------------------------------------------
# Ajuste por máquina / comprador (edite ao copiar para config.py)
# ---------------------------------------------------------------------------
COMPRADOR_PADRAO = "SEU_NOME"
BASE_REDE_DIR = DEFAULT_BASE_REDE_DIR

COMPRADOR_PADRAO = normalizar_usuario(COMPRADOR_PADRAO)

if not COMPRADOR_PADRAO or COMPRADOR_PADRAO == "SEU_NOME":
    raise ValueError(
        "Defina COMPRADOR_PADRAO com seu nome (ex: IURY, THAMYRES, JOAO)"
    )

# Caminhos do comprador na rede
_caminhos = caminhos_comprador(BASE_REDE_DIR, COMPRADOR_PADRAO)
DATABASE_PATH = _caminhos["DATABASE_PATH"]
PEDIDOS_DIR = _caminhos["PEDIDOS_DIR"]
COTACOES_DIR = _caminhos["COTACOES_DIR"]
BACKUP_DIR = _caminhos["BACKUP_DIR"]
RELACOES_DIR = _caminhos["RELACOES_DIR"]

# Timer com o app aberto (0 = desligado)
REDE_SYNC_INTERVALO_SEGUNDOS = int(
    os.environ.get("BRASUL_REDE_SYNC_SEG", str(DEFAULT_REDE_SYNC_INTERVALO_SEGUNDOS))
    or str(DEFAULT_REDE_SYNC_INTERVALO_SEGUNDOS)
)
BACKUP_REDE_INTERVALO_SEGUNDOS = int(
    os.environ.get("BRASUL_BACKUP_REDE_SEG", str(DEFAULT_BACKUP_REDE_INTERVALO_SEGUNDOS))
    or str(DEFAULT_BACKUP_REDE_INTERVALO_SEGUNDOS)
)
REDE_SYNC_CONSOLIDAR_COMPLETO = env_bool(
    "BRASUL_REDE_CONSOLIDAR",
    DEFAULT_REDE_SYNC_CONSOLIDAR_COMPLETO,
)
REDE_SYNC_MESCLAR_CONSOLIDADO = DEFAULT_REDE_SYNC_MESCLAR_CONSOLIDADO

_PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
_loc = configurar_locacoes(_PKG_ROOT)
LOCACOES_PLANILHA_ENV = _loc["LOCACOES_PLANILHA_ENV"]
LOCACOES_PLANILHA_MANUAL = _loc["LOCACOES_PLANILHA_MANUAL"]
LOCACOES_PLANILHA_CANDIDATES = _loc["LOCACOES_PLANILHA_CANDIDATES"]
LOCACOES_AUTO_IMPORT_SE_VAZIO = _loc["LOCACOES_AUTO_IMPORT_SE_VAZIO"]
LOCACOES_AUTO_SYNC_PLANILHA_NOVA = _loc["LOCACOES_AUTO_SYNC_PLANILHA_NOVA"]

# Cria as pastas necessárias automaticamente
for _pasta in (PEDIDOS_DIR, COTACOES_DIR, RELACOES_DIR, BACKUP_DIR):
    os.makedirs(_pasta, exist_ok=True)

# Impede uso acidental deste arquivo como config em produção.
if os.path.basename(os.path.abspath(__file__)).lower() == "config_exemplo.py":
    raise ValueError(
        "Este é o arquivo de exemplo. Copie para config.py, ajuste COMPRADOR_PADRAO "
        "e os caminhos; na cópia o nome do arquivo deixa de ser config_exemplo.py."
    )
