import os
import sqlite3
from datetime import datetime


BASE_REDE = r"Z:\0 OBRAS\brasul_pedidos"
DB_IURY = os.path.join(BASE_REDE, "Iury", "cotacao_iury.db")
DB_THAMYRES = os.path.join(BASE_REDE, "Thamyres", "cotacao_thamyres.db")
DB_REDE = os.path.join(BASE_REDE, "cotacao_rede.db")
BACKUP_DIR = os.path.join(BASE_REDE, "backup_consolidado")


def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M")


def _backup_rede():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f"cotacao_rede_{_ts()}.db")
    with sqlite3.connect(DB_REDE) as src, sqlite3.connect(dst) as out:
        src.backup(out)
    print(f"[OK] Backup do consolidado: {dst}")


def _rows_dict(cur, query, params=()):
    cols = None
    out = []
    for row in cur.execute(query, params):
        if cols is None:
            cols = [d[0] for d in cur.description]
        out.append(dict(zip(cols, row)))
    return out


def _upsert_pedido(dst_conn, pedido):
    numero = str(pedido["numero"] or "").strip()
    comprador = str(pedido.get("comprador") or "").strip().upper()
    if not numero:
        return None, "skip_sem_numero"

    row = dst_conn.execute(
        "SELECT id, comprador FROM pedidos WHERE numero = ?",
        (numero,)
    ).fetchone()

    cols = [
        "data_pedido", "obra_nome", "escola", "fornecedor_nome",
        "fornecedor_razao", "empresa_faturadora", "condicao_pagamento",
        "forma_pagamento", "prazo_entrega", "comprador", "valor_total",
        "caminho_pdf", "status", "emitido_em"
    ]

    if row:
        pedido_id, comprador_existente = row[0], str(row[1] or "").strip().upper()
        if comprador_existente and comprador and comprador_existente != comprador:
            return None, f"conflito_numero:{numero}:{comprador_existente}!={comprador}"

        sets = ", ".join(f"{c}=?" for c in cols)
        vals = [pedido.get(c) for c in cols] + [pedido_id]
        dst_conn.execute(f"UPDATE pedidos SET {sets} WHERE id = ?", vals)
        dst_conn.execute("DELETE FROM itens_pedido WHERE pedido_id = ?", (pedido_id,))
        return pedido_id, "updated"

    insert_cols = ["numero"] + cols
    placeholders = ", ".join("?" for _ in insert_cols)
    vals = [pedido.get(c) for c in insert_cols]
    cur = dst_conn.execute(
        f"INSERT INTO pedidos ({', '.join(insert_cols)}) VALUES ({placeholders})",
        vals,
    )
    return cur.lastrowid, "inserted"


def _copiar_de_origem(db_origem, db_rede_conn):
    origem = sqlite3.connect(db_origem)
    try:
        pedidos = _rows_dict(origem.cursor(), "SELECT * FROM pedidos")
        inseridos = atualizados = conflitos = 0

        for pedido in pedidos:
            novo_id, status = _upsert_pedido(db_rede_conn, pedido)
            if status.startswith("conflito_numero"):
                conflitos += 1
                print(f"[AVISO] {status}")
                continue
            if status == "inserted":
                inseridos += 1
            elif status == "updated":
                atualizados += 1
            if not novo_id:
                continue

            itens = _rows_dict(
                origem.cursor(),
                """
                SELECT descricao, quantidade, unidade, valor_unitario, valor_total, categoria
                  FROM itens_pedido
                 WHERE pedido_id = ?
                """,
                (pedido["id"],),
            )
            for item in itens:
                db_rede_conn.execute(
                    """
                    INSERT INTO itens_pedido
                        (pedido_id, descricao, quantidade, unidade, valor_unitario, valor_total, categoria)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        novo_id,
                        item.get("descricao"),
                        item.get("quantidade"),
                        item.get("unidade"),
                        item.get("valor_unitario"),
                        item.get("valor_total"),
                        item.get("categoria"),
                    ),
                )

        print(
            f"[OK] Origem {os.path.basename(db_origem)}: "
            f"inseridos={inseridos}, atualizados={atualizados}, conflitos={conflitos}"
        )
    finally:
        origem.close()


def main():
    for caminho in (DB_IURY, DB_THAMYRES, DB_REDE):
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    _backup_rede()
    with sqlite3.connect(DB_REDE) as rede:
        rede.execute("PRAGMA foreign_keys = ON")
        _copiar_de_origem(DB_IURY, rede)
        _copiar_de_origem(DB_THAMYRES, rede)
        rede.commit()
    print("[FIM] Consolidação concluída.")


if __name__ == "__main__":
    main()

