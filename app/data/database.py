# app/data/database.py
# Banco local com espelho automático por comprador na rede.
# Modelo:
# - Iury usa banco local e espelha para:      Z:\0 OBRAS\brasul_pedidos\Iury\cotacao_iury.db
# - Thamyres usa banco local e espelha para:  Z:\0 OBRAS\brasul_pedidos\Thamyres\cotacao_thamyres.db
# - Funciona offline: se a rede cair, o sistema continua funcionando localmente.

import os
import shutil
import sqlite3
from datetime import datetime
from config import DATABASE_PATH, BACKUP_DIR


try:
    from config import COMPRADOR_PADRAO
except Exception:
    COMPRADOR_PADRAO = "IURY"


# ============================================================
# CONFIGURAÇÃO DE REDE
# ============================================================
REDE_BASE_DIR = r"Z:\0 OBRAS\brasul_pedidos"


def _normalizar_nome_comprador(nome: str) -> str:
    nome = (nome or "").strip().upper()
    if not nome:
        return "IURY"
    if nome == "YURI":
        return "IURY"
    return nome


def _nome_pasta_comprador(nome: str) -> str:
    nome = _normalizar_nome_comprador(nome)
    return nome.title()


def _nome_arquivo_db_rede(nome: str) -> str:
    nome = _normalizar_nome_comprador(nome)
    slug = "".join(ch.lower() for ch in nome if ch.isalnum()) or "usuario"
    return f"cotacao_{slug}.db"


def obter_rede_db_path() -> str:
    comprador = _normalizar_nome_comprador(COMPRADOR_PADRAO)
    pasta = _nome_pasta_comprador(comprador)
    arquivo = _nome_arquivo_db_rede(comprador)
    return os.path.join(REDE_BASE_DIR, pasta, arquivo)


REDE_DB_PATH = obter_rede_db_path()


# ============================================================
# CONEXÃO
# ============================================================
def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ============================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================
def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS obras (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                nome                TEXT NOT NULL UNIQUE,
                escola              TEXT,
                faturamento         TEXT,
                endereco_entrega    TEXT,
                bairro              TEXT,
                cep                 TEXT,
                cidade              TEXT,
                uf                  TEXT DEFAULT 'SP',
                contrato_obra       TEXT DEFAULT '0',
                empreiteiro         TEXT,
                contato_empreiteiro TEXT,
                ativo               INTEGER DEFAULT 1,
                criado_em           TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS fornecedores (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                nome         TEXT NOT NULL UNIQUE,
                razao_social TEXT,
                email        TEXT,
                vendedor     TEXT,
                telefone     TEXT,
                pix          TEXT,
                favorecido   TEXT,
                ativo        INTEGER DEFAULT 1,
                criado_em    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS pedidos (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                numero              TEXT NOT NULL UNIQUE,
                data_pedido         TEXT,
                obra_nome           TEXT,
                escola              TEXT,
                fornecedor_nome     TEXT,
                fornecedor_razao    TEXT,
                empresa_faturadora  TEXT,
                condicao_pagamento  TEXT,
                forma_pagamento     TEXT,
                prazo_entrega       INTEGER,
                comprador           TEXT,
                valor_total         REAL,
                caminho_pdf         TEXT,
                status              TEXT DEFAULT 'emitido',
                emitido_em          TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS itens_pedido (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id      INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
                descricao      TEXT NOT NULL,
                quantidade     REAL,
                unidade        TEXT,
                valor_unitario REAL,
                valor_total    REAL,
                categoria      TEXT
            );

            CREATE TABLE IF NOT EXISTS cotacoes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                obra_nome       TEXT,
                fornecedor_nome TEXT,
                data_cotacao    TEXT DEFAULT (datetime('now')),
                status          TEXT DEFAULT 'aberta'
            );

            CREATE TABLE IF NOT EXISTS itens_cotacao (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                cotacao_id   INTEGER NOT NULL REFERENCES cotacoes(id) ON DELETE CASCADE,
                descricao    TEXT NOT NULL,
                quantidade   REAL,
                unidade      TEXT,
                preco_f1     REAL,
                preco_f2     REAL,
                preco_f3     REAL,
                fornecedor_1 TEXT,
                fornecedor_2 TEXT,
                fornecedor_3 TEXT
            );

            CREATE TABLE IF NOT EXISTS contador_pedidos (
                id     INTEGER PRIMARY KEY CHECK (id = 1),
                ultimo INTEGER NOT NULL DEFAULT 2548
            );

            INSERT OR IGNORE INTO contador_pedidos (id, ultimo) VALUES (1, 2548);
        """)

    print(f"[DB] Banco inicializado: {DATABASE_PATH}")
    print(f"[REDE] Espelho configurado para: {REDE_DB_PATH}")

    _fazer_backup_se_necessario()
    sincronizar_com_rede(silencioso=True)


# ============================================================
# CONTADOR DE PEDIDOS
# ============================================================
def proximo_numero_pedido():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT ultimo FROM contador_pedidos WHERE id = 1"
        ).fetchone()

        proximo = (row["ultimo"] if row else 2548) + 1
        return str(proximo)


def incrementar_numero_pedido():
    with get_connection() as conn:
        conn.execute(
            "UPDATE contador_pedidos SET ultimo = ultimo + 1 WHERE id = 1"
        )


def atualizar_numero_pedido(numero):
    try:
        n = int(numero)
        with get_connection() as conn:
            conn.execute(
                "UPDATE contador_pedidos SET ultimo = ? WHERE id = 1",
                (n,)
            )
        print(f"[DB] Contador atualizado para {n}")
    except Exception as e:
        print(f"[DB] Erro ao atualizar contador: {e}")


def atualizar_numero_pedido_se_maior(numero):
    """
    Atualiza o contador apenas se o número informado for maior que o atual.
    Evita regressão ao regerar pedidos antigos.
    """
    try:
        n = int(numero)
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE contador_pedidos
                   SET ultimo = CASE WHEN ultimo < ? THEN ? ELSE ultimo END
                 WHERE id = 1
                """,
                (n, n)
            )
        print(f"[DB] Contador verificado com base no pedido {n}")
    except Exception as e:
        print(f"[DB] Erro ao atualizar contador (se maior): {e}")


# ============================================================
# SINCRONIZAÇÃO PARA A REDE
# ============================================================
def sincronizar_com_rede(silencioso=True):
    """
    Se o banco principal já está na rede, não copia nada.
    Evita corromper ou tentar espelhar o arquivo nele mesmo.
    """
    if not REDE_DB_PATH:
        return False

    try:
        origem = os.path.abspath(DATABASE_PATH).lower()
        destino = os.path.abspath(REDE_DB_PATH).lower()

        if origem == destino:
            if not silencioso:
                print("[REDE] Banco principal já está na rede. Sincronização ignorada.")
            return True

        pasta_rede = os.path.dirname(REDE_DB_PATH)
        os.makedirs(pasta_rede, exist_ok=True)

        if not os.path.exists(DATABASE_PATH):
            if not silencioso:
                print("[REDE] Banco local ainda não existe para sincronizar.")
            return False

        shutil.copy2(DATABASE_PATH, REDE_DB_PATH)

        if not silencioso:
            print(f"[REDE] Banco espelhado com sucesso em: {REDE_DB_PATH}")

        return True

    except Exception as e:
        if not silencioso:
            print(f"[REDE] Aviso ao sincronizar: {e}")
        return False


# ============================================================
# BACKUP LOCAL
# ============================================================
def _fazer_backup_se_necessario():
    if not os.path.exists(DATABASE_PATH):
        return

    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)

        semana = datetime.now().strftime("%Y-W%W")
        nome = f"cotacao_backup_{semana}.db"
        caminho = os.path.join(BACKUP_DIR, nome)

        if not os.path.exists(caminho):
            shutil.copy2(DATABASE_PATH, caminho)
            print(f"[DB] Backup criado: {caminho}")
            _limpar_backups_antigos()

    except Exception as e:
        print(f"[DB] Aviso no backup: {e}")


def _limpar_backups_antigos():
    try:
        backups = sorted([
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith("cotacao_backup_") and f.endswith(".db")
        ])

        for antigo in backups[:-8]:
            os.remove(os.path.join(BACKUP_DIR, antigo))

    except Exception:
        pass


# ============================================================
# APOIO / DIAGNÓSTICO
# ============================================================
def info_ambiente_banco():
    return {
        "comprador_padrao": _normalizar_nome_comprador(COMPRADOR_PADRAO),
        "database_local": DATABASE_PATH,
        "database_rede": REDE_DB_PATH,
        "rede_base_dir": REDE_BASE_DIR,
    }

def obter_pasta_rede_usuario():
    comprador = _normalizar_nome_comprador(COMPRADOR_PADRAO)
    pasta = _nome_pasta_comprador(comprador)
    return os.path.join(REDE_BASE_DIR, pasta)


def copiar_arquivo_para_rede(caminho_origem, subpasta):
    try:
        base = obter_pasta_rede_usuario()
        destino_dir = os.path.join(base, subpasta)
        os.makedirs(destino_dir, exist_ok=True)

        nome = os.path.basename(caminho_origem)
        destino = os.path.join(destino_dir, nome)

        shutil.copy2(caminho_origem, destino)
        print(f"[REDE] Arquivo copiado: {destino}")
    except Exception as e:
        print(f"[REDE] Erro ao copiar arquivo: {e}")