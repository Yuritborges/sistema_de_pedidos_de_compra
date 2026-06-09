# app/config/__init__.py
# Constantes compartilhadas do sistema (independente do config.py local de cada máquina).

from app.config.settings import (
    APP_NAME,
    APP_VERSION,
    CATEGORIAS_ITEM,
    CONDICOES_PAGAMENTO,
    DEBUG,
    EMPRESAS_FATURADORAS,
    FORMAS_PAGAMENTO,
    ORGANIZATION_NAME,
    THEME,
    UNIDADES,
    caminhos_comprador,
    configurar_locacoes,
    env_bool,
    is_debug_mode,
    normalizar_usuario,
    slug_usuario,
)

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "ORGANIZATION_NAME",
    "DEBUG",
    "THEME",
    "EMPRESAS_FATURADORAS",
    "CATEGORIAS_ITEM",
    "UNIDADES",
    "CONDICOES_PAGAMENTO",
    "FORMAS_PAGAMENTO",
    "env_bool",
    "is_debug_mode",
    "normalizar_usuario",
    "slug_usuario",
    "caminhos_comprador",
    "configurar_locacoes",
]
