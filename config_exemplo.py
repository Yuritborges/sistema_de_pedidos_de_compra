# config.py
# Configurações gerais do sistema: empresas, caminhos, constantes etc.

import os

COMPRADOR_PADRAO = "SEU_NOME"
PASTA_COMPRADOR = "SuaPasta"

COMPRADOR_PADRAO = COMPRADOR_PADRAO.strip().upper()
PASTA_COMPRADOR = PASTA_COMPRADOR.strip()

if not COMPRADOR_PADRAO or COMPRADOR_PADRAO == "SEU_NOME":
    raise ValueError("Defina COMPRADOR_PADRAO com seu nome (ex: IURY, THAMYRES, JOAO)")

if not PASTA_COMPRADOR or PASTA_COMPRADOR == "SuaPasta":
    raise ValueError("Defina PASTA_COMPRADOR com o nome da pasta (ex: Iury, Thamyres, Joao)")

raise ValueError(
    "Arquivo de exemplo. Copie para config.py e configure antes de rodar o sistema."
)

DATABASE_PATH = r"Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db"
PEDIDOS_DIR = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\pdfs de pedidos"
COTACOES_DIR = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\cotações_salvas"
BACKUP_DIR = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\backup"
RELACOES_DIR = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\relações"


# Cria as pastas necessárias automaticamente
for _pasta in [PEDIDOS_DIR, COTACOES_DIR, RELACOES_DIR, BACKUP_DIR]:
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
        "endereco":     "Av. Independência, 546 sala 93 – Cidade Alta – Piracicaba, SP - CEP 13419-160",
        "telefone":     "(11) 3641-9169",
        "email":        "compra2@construtorainteriorana.com.br",
        "logo":         "logo_interiorana.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nINTERIORANA CONSTRUTORA LTDA",
        "cor_header":   (100, 50, 0),
    },
    "INTERBRAS": {
        "razao_social": "CONSÓRCIO INTERBRAS",
        "endereco":     "Rua Coronel Jordão, 440, Vila Paiva - São Paulo, SP - CEP 02075-030",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "logo":         "logo_interbras.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nINTERBRAS CONSTRUTORA LTDA",
        "cor_header":   (50, 50, 130),
    },
}

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
