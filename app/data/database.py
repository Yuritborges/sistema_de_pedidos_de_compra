# app/data/database.py
# Cria e gerencia o banco de dados SQLite do sistema.

import sqlite3
import os
from config import DATABASE_PATH


def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    # Cria todas as tabelas se ainda não existirem
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
                pedido_id      INTEGER NOT NULL REFERENCES pedidos(id),
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
                cotacao_id   INTEGER NOT NULL REFERENCES cotacoes(id),
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


def proximo_numero_pedido():
    # Pega o próximo número disponível e já incrementa no banco
    with get_connection() as conn:
        row = conn.execute("SELECT ultimo FROM contador_pedidos WHERE id=1").fetchone()
        proximo = (row["ultimo"] if row else 2548) + 1
        conn.execute("UPDATE contador_pedidos SET ultimo=? WHERE id=1", (proximo,))
    return str(proximo)
