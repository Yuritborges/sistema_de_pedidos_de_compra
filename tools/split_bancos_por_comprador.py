import os
import sqlite3


SOURCE_DB = r"Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db"
OUTPUT_DIR = r"Z:\0 OBRAS\sistema_de_pedidos_brasulv2\database\bootstrap"

TARGETS = [
    ("IURY", {"IURY", "YURI"}),
    ("THAMYRES", {"THAMYRES"}),
]


def _comprador_expr():
    return "UPPER(TRIM(IFNULL(comprador, '')))"


def _count_pedidos(conn):
    return conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]


def _count_itens(conn):
    return conn.execute("SELECT COUNT(*) FROM itens_pedido").fetchone()[0]


def _max_numero(conn):
    row = conn.execute(
        """
        SELECT COALESCE(MAX(CAST(numero AS INTEGER)), 2548)
          FROM pedidos
         WHERE TRIM(IFNULL(numero, '')) <> ''
           AND TRIM(numero) GLOB '[0-9]*'
        """
    ).fetchone()
    return int(row[0] if row and row[0] is not None else 2548)


def _build_for_user(user_name, aliases):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"cotacao_{user_name.lower()}.db")
    if os.path.exists(out_path):
        os.remove(out_path)

    with sqlite3.connect(SOURCE_DB) as src, sqlite3.connect(out_path) as dst:
        src.backup(dst)

    aliases_sql = ", ".join(f"'{a}'" for a in sorted(aliases))
    where_keep = f"{_comprador_expr()} IN ({aliases_sql})"

    with sqlite3.connect(out_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute(f"DELETE FROM pedidos WHERE NOT ({where_keep})")
        conn.execute(
            """
            DELETE FROM itens_pedido
             WHERE pedido_id NOT IN (SELECT id FROM pedidos)
            """
        )

        ultimo = _max_numero(conn)
        conn.execute("UPDATE contador_pedidos SET ultimo = ? WHERE id = 1", (ultimo,))
        conn.commit()
        conn.execute("VACUUM")

        pedidos = _count_pedidos(conn)
        itens = _count_itens(conn)

    return out_path, pedidos, itens, ultimo


def main():
    if not os.path.exists(SOURCE_DB):
        raise FileNotFoundError(f"Banco de origem não encontrado: {SOURCE_DB}")

    print(f"[OK] Origem: {SOURCE_DB}")
    print(f"[OK] Saída:  {OUTPUT_DIR}")

    for user, aliases in TARGETS:
        path, qtd_pedidos, qtd_itens, ultimo = _build_for_user(user, aliases)
        print(
            f"[OK] {user}: pedidos={qtd_pedidos}, itens={qtd_itens}, "
            f"ultimo={ultimo}, arquivo={path}"
        )


if __name__ == "__main__":
    main()
