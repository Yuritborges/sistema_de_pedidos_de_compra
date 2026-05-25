"""
Remove modo WAL dos .db na rede (causa travamentos com vários PCs no Z:).

Feche o Sistema de Pedidos em TODOS os computadores antes de rodar:
  python tools/fix_sqlite_journal_rede.py
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE = Path(r"Z:\0 OBRAS\brasul_pedidos")
ARQUIVOS = [
    BASE / "Iury" / "cotacao_iury.db",
    BASE / "Thamyres" / "cotacao_thamyres.db",
    BASE / "cotacao_rede.db",
    BASE / "_shared" / "locacoes.db",
]


def corrigir(caminho: Path) -> None:
    if not caminho.is_file():
        print(f"[PULAR] Nao existe: {caminho}")
        return
    wal = Path(str(caminho) + "-wal")
    shm = Path(str(caminho) + "-shm")
    try:
        with sqlite3.connect(str(caminho), timeout=20) as conn:
            conn.execute("PRAGMA busy_timeout = 8000")
            antes = conn.execute("PRAGMA journal_mode").fetchone()[0]
            conn.execute("PRAGMA journal_mode = DELETE")
            depois = conn.execute("PRAGMA journal_mode").fetchone()[0]
        print(f"[OK] {caminho.name}: {antes} -> {depois}")
        for extra in (wal, shm):
            if extra.is_file():
                try:
                    extra.unlink()
                    print(f"      removido {extra.name}")
                except OSError as e:
                    print(f"      aviso {extra.name}: {e}")
    except sqlite3.OperationalError as e:
        print(f"[ERRO] {caminho}: {e}")
        print("       Feche o programa em todos os PCs e tente de novo.")


def main() -> int:
    print("Corrigindo journal_mode (WAL -> DELETE) na rede...")
    for p in ARQUIVOS:
        corrigir(p)
    print("[FIM] Concluido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
