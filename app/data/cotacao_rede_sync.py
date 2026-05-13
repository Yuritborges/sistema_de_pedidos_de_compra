# app/data/cotacao_rede_sync.py
# Consolidação em cotacao_rede.db: merge completo (script) + atualização incremental após salvar pedido.

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

from config import BASE_REDE_DIR

BASE_REDE = os.path.normpath(BASE_REDE_DIR)
DB_IURY = os.path.join(BASE_REDE, "Iury", "cotacao_iury.db")
DB_THAMYRES = os.path.join(BASE_REDE, "Thamyres", "cotacao_thamyres.db")
DB_REDE = os.path.join(BASE_REDE, "cotacao_rede.db")
BACKUP_DIR = os.path.join(BASE_REDE, "backup_consolidado")


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")


def parse_val(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def rows_dict(cur, query, params=()):
    cols = None
    out = []
    for row in cur.execute(query, params):
        if cols is None:
            cols = [d[0] for d in cur.description]
        out.append(dict(zip(cols, row)))
    return out


def parse_emitido(raw):
    s = str(raw or "").strip()
    if not s:
        return datetime.min
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d/%m/%Y",
        "%d/%m/%y",
    ):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def upsert_pedido(dst_conn, pedido):
    numero = str(pedido["numero"] or "").strip()
    comprador = str(pedido.get("comprador") or "").strip().upper()
    if not numero:
        return None, "skip_sem_numero"

    row = dst_conn.execute(
        "SELECT id, comprador, emitido_em, valor_total FROM pedidos WHERE numero = ?",
        (numero,),
    ).fetchone()

    cols = [
        "data_pedido",
        "obra_nome",
        "escola",
        "fornecedor_nome",
        "fornecedor_razao",
        "empresa_faturadora",
        "condicao_pagamento",
        "forma_pagamento",
        "pagamento_etapas_ativo",
        "percentual_entrada",
        "percentual_final",
        "marco_percentual_final",
        "prazo_entrega",
        "comprador",
        "valor_total",
        "desconto",
        "desconto_tipo",
        "desconto_valor_digitado",
        "caminho_pdf",
        "status",
        "emitido_em",
        "material_entregue_em",
    ]
    cols_destino = {r[1] for r in dst_conn.execute("PRAGMA table_info(pedidos)").fetchall()}
    cols = [c for c in cols if c in cols_destino and c in pedido]

    if row:
        pedido_id, comprador_existente = row[0], str(row[1] or "").strip().upper()
        if comprador_existente and comprador and comprador_existente != comprador:
            atual_emit = parse_emitido(row[2])
            novo_emit = parse_emitido(pedido.get("emitido_em"))
            atual_val = parse_val(row[3])
            novo_val = parse_val(pedido.get("valor_total"))
            if (novo_emit > atual_emit) or (
                novo_emit == atual_emit and abs(novo_val) > abs(atual_val)
            ):
                pass
            else:
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


def merge_origem_path_into_rede(db_rede_conn, db_origem_path: str) -> None:
    origem = sqlite3.connect(db_origem_path)
    try:
        pedidos = rows_dict(origem.cursor(), "SELECT * FROM pedidos")
        inseridos = atualizados = conflitos = 0

        for pedido in pedidos:
            novo_id, status = upsert_pedido(db_rede_conn, pedido)
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

            itens = rows_dict(
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
            f"[OK] Origem {os.path.basename(db_origem_path)}: "
            f"inseridos={inseridos}, atualizados={atualizados}, conflitos={conflitos}"
        )
    finally:
        origem.close()


def backup_cotacao_rede() -> None:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f"cotacao_rede_{_ts()}.db")
    with sqlite3.connect(DB_REDE) as src, sqlite3.connect(dst) as out:
        src.backup(out)
    print(f"[OK] Backup do consolidado: {dst}")


def run_full_consolidation() -> None:
    for caminho in (DB_IURY, DB_THAMYRES, DB_REDE):
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    backup_cotacao_rede()
    with sqlite3.connect(DB_REDE) as rede:
        rede.execute("PRAGMA foreign_keys = ON")
        merge_origem_path_into_rede(rede, DB_IURY)
        merge_origem_path_into_rede(rede, DB_THAMYRES)
        rede.commit()
    print("[FIM] Consolidação concluída.")


def _rede_sync_disabled() -> bool:
    v = (os.environ.get("BRASUL_SKIP_COTACAO_REDE_SYNC") or "").strip().lower()
    return v in ("1", "true", "yes", "sim")


def sync_pedido_atual_para_cotacao_rede(numero: str) -> bool:
    """
    Após salvar no banco do comprador, replica o pedido (e itens) em cotacao_rede.db.
    Mesma regra de upsert do merge completo; não cria backup (operação leve).
    """
    if _rede_sync_disabled():
        return False
    numero = str(numero or "").strip()
    if not numero or not os.path.isfile(DB_REDE):
        return False

    from app.data.database import get_connection

    try:
        with get_connection() as src:
            row = src.execute(
                "SELECT * FROM pedidos WHERE numero = ?",
                (numero,),
            ).fetchone()
            if not row:
                return False
            pedido = dict(row)
            src_pid = pedido["id"]
            itens = rows_dict(
                src,
                """
                SELECT descricao, quantidade, unidade, valor_unitario, valor_total, categoria
                  FROM itens_pedido
                 WHERE pedido_id = ?
                """,
                (src_pid,),
            )
    except Exception as e:
        print(f"[REDE] cotacao_rede incremental (leitura): {e}")
        return False

    rede = sqlite3.connect(DB_REDE, timeout=30)
    rede.row_factory = sqlite3.Row
    try:
        rede.execute("PRAGMA foreign_keys = ON")
        rede.execute("PRAGMA busy_timeout = 30000")
        novo_id, status = upsert_pedido(rede, pedido)
        if status.startswith("conflito_numero"):
            print(f"[REDE] cotacao_rede incremental: {status}")
            rede.rollback()
            return False
        if not novo_id:
            rede.rollback()
            return False
        for item in itens:
            rede.execute(
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
        rede.commit()
        return True
    except Exception as e:
        print(f"[REDE] cotacao_rede incremental (gravação): {e}")
        try:
            rede.rollback()
        except Exception:
            pass
        return False
    finally:
        rede.close()


def merge_local_database_para_rede_consolidado(silencioso: bool = True) -> bool:
    """
    Mescla o SQLite local do comprador (DATABASE_PATH) no cotacao_rede.db.
    Chamado pelo tick periódico quando REDE_SYNC_MESCLAR_CONSOLIDADO está ativo.
    """
    if _rede_sync_disabled():
        return False
    try:
        from app.data.database import DATABASE_PATH as _local_db
    except Exception:
        return False

    local_path = os.path.abspath(_local_db)
    if not os.path.isfile(DB_REDE) or not os.path.isfile(local_path):
        return False
    if os.path.abspath(DB_REDE).lower() == local_path.lower():
        return True

    rede = None
    try:
        rede = sqlite3.connect(DB_REDE, timeout=30)
        rede.row_factory = sqlite3.Row
        rede.execute("PRAGMA foreign_keys = ON")
        rede.execute("PRAGMA busy_timeout = 30000")
        merge_origem_path_into_rede(rede, local_path)
        rede.commit()
        return True
    except Exception as e:
        if not silencioso:
            print(f"[REDE] merge consolidado: {e}")
        if rede is not None:
            try:
                rede.rollback()
            except Exception:
                pass
        return False
    finally:
        if rede is not None:
            try:
                rede.close()
            except Exception:
                pass


def remover_pedido_cotacao_rede(numero: str) -> bool:
    """Remove o pedido do consolidado após exclusão no banco do comprador."""
    if _rede_sync_disabled():
        return False
    numero = str(numero or "").strip()
    if not numero or not os.path.isfile(DB_REDE):
        return False
    rede = sqlite3.connect(DB_REDE, timeout=30)
    try:
        rede.execute("PRAGMA busy_timeout = 30000")
        row = rede.execute(
            "SELECT id FROM pedidos WHERE numero = ?",
            (numero,),
        ).fetchone()
        if not row:
            rede.commit()
            return True
        pid = row[0]
        rede.execute("DELETE FROM itens_pedido WHERE pedido_id = ?", (pid,))
        rede.execute("DELETE FROM pedidos WHERE id = ?", (pid,))
        rede.commit()
        return True
    except Exception as e:
        print(f"[REDE] cotacao_rede remover: {e}")
        try:
            rede.rollback()
        except Exception:
            pass
        return False
    finally:
        rede.close()
