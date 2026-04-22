# config.py
# Configurações gerais do sistema: empresas, caminhos, categorias etc.

import os

# Caminhos principais do projeto
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "cotacao.db")
PEDIDOS_DIR   = os.path.join(BASE_DIR, "pedidos_gerados")
ASSETS_DIR    = os.path.join(BASE_DIR, "assets")
LOGOS_DIR     = os.path.join(ASSETS_DIR, "logos")
COTACOES_DIR  = os.path.join(ASSETS_DIR, "cotacoes_salvas")
BACKUP_DIR    = os.path.join(BASE_DIR, "database", "backup")

# Cria as pastas necessárias automaticamente
for _pasta in [PEDIDOS_DIR, COTACOES_DIR, BACKUP_DIR]:
    os.makedirs(_pasta, exist_ok=True)

# Dados de cada empresa faturadora
EMPRESAS_FATURADORAS = {
    "BRASUL": {
        "razao_social": "BRASUL CONSTRUTORA LTDA",
        "endereco":     "Rua Coronel Jordão, 440, Vila Paiva - São Paulo, SP - CEP 02075-030",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "logo":         "logo_brasul.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nBRASUL CONSTRUTORA LTDA",
        "cor_header":   (0, 51, 102),
    },
    "JB": {
        "razao_social": "JB CONSTRUÇÕES E EMPREENDIMENTOS LTDA",
        "endereco":     "Av Luis Dummount Vilares 2078, São Paulo, SP - CEP 02239-000",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "logo":         "logo_jb.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nJB CONSTRUÇÕES E EMPREENDIMENTOS LTDA",
        "cor_header":   (180, 0, 0),
    },
    "B&B": {
        "razao_social": "B & B Engenharia e Construções LTDA",
        "endereco":     "Rua Itamonte 33, Vila Medeiros - São Paulo, SP - CEP 02220-000",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "logo":         "logo_bb.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nB&B Engenharia e Construções LTDA",
        "cor_header":   (0, 100, 0),
    },
    "INTERIORANA": {
        "razao_social": "INTERIORANA CONSTRUTORA LTDA",
        "endereco":     "Avª Mofarrej, 348 – Sala 703 – Vila Leopoldina – São Paulo/SP",
        "telefone":     "(11) 2892.8916",
        "email":        "compra2@construtorainteriorana.com.br",
        "logo":         "logo_interiorana.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nINTERIORANA CONSTRUTORA LTDA",
        "cor_header":   (100, 50, 0),
    },
    "INTERBRAS": {
        "razao_social": "CONSÓRCIO INTERBRAS",
        "endereco":     "São Paulo, SP",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "logo":         "logo_interbras.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nINTERBRAS CONSTRUTORA LTDA",
        "cor_header":   (50, 50, 130),
    },
}

COMPRADOR_PADRAO = "IURY"

CATEGORIAS_ITEM = [
    "FUNDAÇÃO / ESTRUTURA",
    "COBERTURA / FORRO",
    "HIDRAULICA",
    "ELETRICA",
    "REVESTMENTO / PISO",
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
