import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB_ORIGEM = r"Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db"
DB_DESTINO = r"Z:\0 OBRAS\brasul_pedidos\Iury\cotacao_iury.db"
COMPRADOR = "IURY"


def mover_banco_ruim():
    if os.path.exists(DB_DESTINO):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruim = DB_DESTINO.replace(".db", f"_corrompido_{stamp}.db")
        shutil.move(DB_DESTINO, ruim)
        print(f"Banco ruim movido para: {ruim}")


def criar_schema():
    conn = sqlite3.connect(DB_DESTINO)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            escola TEXT,
            faturamento TEXT,
            endereco_entrega TEXT,
            bairro TEXT,
            cep TEXT,
            cidade TEXT,
            uf TEXT DEFAULT 'SP',
            contrato_obra TEXT DEFAULT '0',
            empreiteiro TEXT,
            contato_empreiteiro TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            razao_social TEXT,
            email TEXT,
            vendedor TEXT,
            telefone TEXT,
            pix TEXT,
            favorecido TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            data_pedido TEXT,
            obra_nome TEXT,
            escola TEXT,
            fornecedor_nome TEXT,
            fornecedor_razao TEXT,
            empresa_faturadora TEXT,
            condicao_pagamento TEXT,
            forma_pagamento TEXT,
            prazo_entrega INTEGER,
            comprador TEXT,
            valor_total REAL,
            caminho_pdf TEXT,
            status TEXT DEFAULT 'emitido',
            emitido_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
            descricao TEXT NOT NULL,
            quantidade REAL,
            unidade TEXT,
            valor_unitario REAL,
            valor_total REAL,
            categoria TEXT
        );

        CREATE TABLE IF NOT EXISTS contador_pedidos (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            ultimo INTEGER NOT NULL DEFAULT 2548
        );

        INSERT OR IGNORE INTO contador_pedidos (id, ultimo) VALUES (1, 2548);
    """)
    conn.commit()
    conn.close()


def colunas(conn, tabela):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({tabela})")]


def tabelas(conn):
    return {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def copiar_por_colunas(conn_o, conn_d, tabela, where_sql="", params=()):
    if tabela not in tabelas(conn_o) or tabela not in tabelas(conn_d):
        return 0

    cols_o = colunas(conn_o, tabela)
    cols_d = colunas(conn_d, tabela)
    comuns = [c for c in cols_o if c in cols_d]

    if not comuns:
        return 0

    rows = conn_o.execute(
        f"SELECT {', '.join(comuns)} FROM {tabela} {where_sql}",
        params
    ).fetchall()

    ph = ", ".join(["?"] * len(comuns))

    for row in rows:
        conn_d.execute(
            f"""
            INSERT OR IGNORE INTO {tabela}
            ({', '.join(comuns)})
            VALUES ({ph})
            """,
            tuple(row)
        )

    return len(rows)


def main():
    if not Path(DB_ORIGEM).exists():
        raise FileNotFoundError(f"Banco origem não encontrado: {DB_ORIGEM}")

    os.makedirs(os.path.dirname(DB_DESTINO), exist_ok=True)

    mover_banco_ruim()
    criar_schema()

    conn_o = sqlite3.connect(DB_ORIGEM)
    conn_d = sqlite3.connect(DB_DESTINO)
    conn_o.row_factory = sqlite3.Row
    conn_d.row_factory = sqlite3.Row

    try:
        print("Importando dados do IURY...")

        pedidos_ids = [
            r["id"] for r in conn_o.execute(
                """
                SELECT id FROM pedidos
                WHERE UPPER(COALESCE(comprador, '')) IN ('IURY', 'YURI')
                """
            ).fetchall()
        ]

        if pedidos_ids:
            ph_ids = ", ".join(["?"] * len(pedidos_ids))

            print("Pedidos:", copiar_por_colunas(
                conn_o, conn_d, "pedidos",
                f"WHERE id IN ({ph_ids})",
                pedidos_ids
            ))

            print("Itens:", copiar_por_colunas(
                conn_o, conn_d, "itens_pedido",
                f"WHERE pedido_id IN ({ph_ids})",
                pedidos_ids
            ))

        print("Obras:", copiar_por_colunas(conn_o, conn_d, "obras"))
        print("Fornecedores:", copiar_por_colunas(conn_o, conn_d, "fornecedores"))

        # Ajuste aqui se seu último pedido for outro
        ultimo_iury = conn_d.execute("""
            SELECT MAX(CAST(numero AS INTEGER))
            FROM pedidos
            WHERE numero GLOB '[0-9]*'
        """).fetchone()[0]

        if ultimo_iury:
            conn_d.execute(
                "UPDATE contador_pedidos SET ultimo = ? WHERE id = 1",
                (int(ultimo_iury),)
            )
            print(f"Contador ajustado para: {ultimo_iury}")

        conn_d.commit()
        print("Banco do Iury recriado com sucesso.")

    except Exception:
        conn_d.rollback()
        raise
    finally:
        conn_o.close()
        conn_d.close()


if __name__ == "__main__":
    main()