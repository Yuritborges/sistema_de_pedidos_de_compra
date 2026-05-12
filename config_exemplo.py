# config_exemplo.py — modelo para gerar config.py (não use este nome em produção).
# Copie para config.py, edite COMPRADOR_PADRAO / PASTA_COMPRADOR e caminhos; o guard no final só roda neste arquivo modelo.

import os

COMPRADOR_PADRAO = "SEU_NOME"
PASTA_COMPRADOR = "SuaPasta"

COMPRADOR_PADRAO = COMPRADOR_PADRAO.strip().upper()
PASTA_COMPRADOR = PASTA_COMPRADOR.strip()

if not COMPRADOR_PADRAO or COMPRADOR_PADRAO == "SEU_NOME":
    raise ValueError("Defina COMPRADOR_PADRAO com seu nome (ex: IURY, THAMYRES, JOAO)")

if not PASTA_COMPRADOR or PASTA_COMPRADOR == "SuaPasta":
    raise ValueError("Defina PASTA_COMPRADOR com o nome da pasta (ex: Iury, Thamyres, Joao)")

# Banco de trabalho do comprador (não use cotacao_rede.db aqui; esse arquivo é o consolidado na rede).
DATABASE_PATH = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\cotacao_{''.join(ch.lower() for ch in COMPRADOR_PADRAO if ch.isalnum())}.db"
# Pasta raiz da rede (Iury/Thamyres/cotacao_rede.db, cadastros compartilhados, etc.).
BASE_REDE_DIR = r"Z:\0 OBRAS\brasul_pedidos"
PEDIDOS_DIR = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\pdfs de pedidos"
COTACOES_DIR = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\cotações_salvas"
BACKUP_DIR = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\backup"
RELACOES_DIR = fr"Z:\0 OBRAS\brasul_pedidos\{PASTA_COMPRADOR}\relações"

# 0 = desligado. Ex.: 30 = a cada 30 s copia o SQLite do comprador para a pasta na rede (cadastros/obras/pedidos no .db do comprador).
REDE_SYNC_INTERVALO_SEGUNDOS = 0
# Se True, no mesmo gatilho roda em thread a reaplicação de todos os pedidos locais em cotacao_rede.db (mais pesado; salvar pedido já faz sync incremental).
REDE_SYNC_MESCLAR_CONSOLIDADO = False


# Cria as pastas necessárias automaticamente
for _pasta in [PEDIDOS_DIR, COTACOES_DIR, RELACOES_DIR, BACKUP_DIR]:
    os.makedirs(_pasta, exist_ok=True)

# Dados de cada empresa faturadora
# email_rodape_1 / email_rodape_2: rodapé do PDF "Notas e Boletos encaminha para:"
EMPRESAS_FATURADORAS = {
    "BRASUL": {
        "razao_social": "BRASUL CONSTRUTORA LTDA",
        "endereco":     "Rua Coronel Jordão, 440, Vila Paiva - São Paulo, SP - CEP 02075-030",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "viviane@brasulconstrutora.com.br",
        "logo":         "logo_brasul.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nBRASUL CONSTRUTORA LTDA",
        "cor_header":   (0, 51, 102),
    },
    "JB": {
        "razao_social": "JB CONSTRUÇÕES E EMPREENDIMENTOS LTDA",
        "endereco":     "Av Luis Dummount Vilares 2078, São Paulo, SP - CEP 02239-000",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "viviane@brasulconstrutora.com.br",
        "logo":         "logo_jb.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nJB CONSTRUÇÕES E EMPREENDIMENTOS LTDA",
        "cor_header":   (180, 0, 0),
    },
    "B&B": {
        "razao_social": "B & B Engenharia e Construções LTDA",
        "endereco":     "Rua Itamonte 33, Vila Medeiros - São Paulo, SP - CEP 02220-000",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "viviane@brasulconstrutora.com.br",
        "logo":         "logo_bb.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nB&B Engenharia e Construções LTDA",
        "cor_header":   (0, 100, 0),
    },
    "INTERIORANA": {
        "razao_social": "INTERIORANA CONSTRUTORA LTDA",
        "endereco":     "Av. Independência, 546 sala 93 – Cidade Alta – Piracicaba, SP - CEP 13419-160",
        "telefone":     "(11) 3641-9169",
        "email":        "compra2@construtorainteriorana.com.br",
        "email_rodape_1": "notafiscal@construtorainteriorana.com.br",
        "email_rodape_2": "financeiro2@construtorainteriorana.com.br",
        "logo":         "logo_interiorana.png",
        "obs_padrao":   "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\nINTERIORANA CONSTRUTORA LTDA",
        "cor_header":   (100, 50, 0),
    },
    "INTERBRAS": {
        "razao_social": "CONSÓRCIO INTERBRAS",
        "endereco":     "Rua Coronel Jordão, 440, Vila Paiva - São Paulo, SP - CEP 02075-030",
        "telefone":     "(11) 3313-8220",
        "email":        "compras2@brasulconstrutora.com.br",
        "email_rodape_1": "notafiscal@brasulconstrutora.com.br",
        "email_rodape_2": "viviane@brasulconstrutora.com.br",
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

# Impede uso acidental deste arquivo como config em produção (só quando o nome do arquivo continua config_exemplo.py).
if os.path.basename(os.path.abspath(__file__)).lower() == "config_exemplo.py":
    raise ValueError(
        "Este é o arquivo de exemplo. Copie para config.py, ajuste COMPRADOR_PADRAO, "
        "PASTA_COMPRADOR e os caminhos abaixo; na cópia o nome do arquivo deixa de ser config_exemplo.py."
    )
