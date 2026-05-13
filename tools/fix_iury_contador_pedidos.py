"""
Correção pontual: dois pedidos antigos (6098/6094-12-2024) elevavam o MAX(numero)
e o próximo sugerido ia para 6100. Renumeram-se para prefixo ARC (fora do GLOB só-dígitos
em proximo_numero_pedido) e o contador fica em 2667 → próximo 2668.

Uso (na raiz do repo):
  set BRASUL_USUARIO=IURY
  python tools/fix_iury_contador_pedidos.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import config as cfg  # noqa: E402

TARGET_NEXT = 2668
TARGET_ULTIMO = TARGET_NEXT - 1
# Pedidos que quebram a sequência 26xx (Dec/2024 — RENT MAX); não apagamos, só marcamos como legado no Nº.
IDS_LEGADO = (2531, 2532)
NUM_LEGADO = ("ARC6098", "ARC6099")


def main() -> int:
    path = cfg.DATABASE_PATH
    print("Banco:", path)
    if not os.path.isfile(path):
        print("ERRO: ficheiro não encontrado")
        return 1

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        mx_row = conn.execute(
            """
            SELECT COALESCE(MAX(CAST(numero AS INTEGER)), 0)
              FROM pedidos
             WHERE TRIM(IFNULL(numero, '')) <> ''
               AND TRIM(numero) GLOB '[0-9]*'
            """
        ).fetchone()
        mx = int(mx_row[0] or 0)
        cur = conn.execute("SELECT ultimo FROM contador_pedidos WHERE id = 1").fetchone()
        antes = int(cur["ultimo"]) if cur and cur["ultimo"] is not None else None
        print("MAX(pedidos.numero) [só dígitos]:", mx)
        print("contador.ultimo (antes):", antes)

        if mx <= TARGET_ULTIMO and antes == TARGET_ULTIMO:
            print("Nada a fazer: sequência já coerente com próximo", TARGET_NEXT)
            return 0

        for pid, novo_num in zip(IDS_LEGADO, NUM_LEGADO):
            row = conn.execute(
                "SELECT id, numero FROM pedidos WHERE id = ?", (pid,)
            ).fetchone()
            if not row:
                print(f"AVISO: pedido id={pid} não encontrado — ignorado")
                continue
            if str(row["numero"]) in NUM_LEGADO:
                print(f"Pedido {pid} já está como {row['numero']} — ignorado")
                continue
            conn.execute(
                "UPDATE pedidos SET numero = ? WHERE id = ?",
                (novo_num, pid),
            )
            print(f"Pedido id={pid}: número {row['numero']!r} -> {novo_num!r} (legado, fora da sequência numérica)")

        mx_row2 = conn.execute(
            """
            SELECT COALESCE(MAX(CAST(numero AS INTEGER)), 0)
              FROM pedidos
             WHERE TRIM(IFNULL(numero, '')) <> ''
               AND TRIM(numero) GLOB '[0-9]*'
            """
        ).fetchone()
        mx2 = int(mx_row2[0] or 0)
        novo_cont = max(TARGET_ULTIMO, mx2)
        conn.execute(
            "UPDATE contador_pedidos SET ultimo = ? WHERE id = 1",
            (novo_cont,),
        )
        conn.commit()
        print("MAX após ajuste:", mx2)
        print("contador.ultimo (depois):", novo_cont)
        prox = max(novo_cont, mx2) + 1
        print("Próximo número (fórmula do programa):", prox)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
