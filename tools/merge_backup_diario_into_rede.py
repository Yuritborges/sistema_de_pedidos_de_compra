"""
Mescla os bancos do backup diario (Iury + Thamyres) no cotacao_rede.db da rede,
usando a mesma logica de consolidar_rede.py.

Use quando o consolidado estiver defasado mas voces tiverem um backup de horario
conhecido (ex.: hoje 18:00 em backups/diario/iury_YYYYMMDD_HHMM.db).

Uso (na raiz do projeto de pedidos, com venv):
  .\\.venv\\Scripts\\python.exe tools\\merge_backup_diario_into_rede.py
  .\\.venv\\Scripts\\python.exe tools\\merge_backup_diario_into_rede.py --ts 20260507_1800
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from consolidar_rede import DB_REDE, _backup_rede, _copiar_de_origem  # noqa: E402

BASE_PROJETO = os.path.dirname(_TOOLS_DIR)
BACKUP_DIARIO = os.path.join(BASE_PROJETO, "backups", "diario")


def _listar_ts_disponiveis():
    if not os.path.isdir(BACKUP_DIARIO):
        return []
    r = re.compile(r"^iury_(\d{8}_\d{4})\.db$")
    ts_list = []
    for nome in os.listdir(BACKUP_DIARIO):
        m = r.match(nome)
        if m:
            ts_list.append(m.group(1))
    return sorted(ts_list, reverse=True)


def _resolver_ts(explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    disponiveis = _listar_ts_disponiveis()
    if not disponiveis:
        raise FileNotFoundError(f"Nenhum iury_*.db em {BACKUP_DIARIO}")
    escolhido = disponiveis[0]
    print(f"[INFO] Usando ultimo backup diario encontrado: {escolhido}")
    return escolhido


def main():
    ap = argparse.ArgumentParser(description="Mescla backup diario Iury+Thamyres no cotacao_rede.db")
    ap.add_argument(
        "--ts",
        help="Timestamp do backup (ex.: 20260507_1800). Omited: o mais recente em backups/diario.",
        default=None,
    )
    args = ap.parse_args()

    ts = _resolver_ts(args.ts)
    bi = os.path.join(BACKUP_DIARIO, f"iury_{ts}.db")
    bt = os.path.join(BACKUP_DIARIO, f"thamyres_{ts}.db")

    for label, path in (("Iury", bi), ("Thamyres", bt)):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Arquivo de backup nao encontrado ({label}): {path}")

    if not os.path.isfile(DB_REDE):
        raise FileNotFoundError(f"cotacao_rede.db nao encontrado: {DB_REDE}")

    print(f"[INICIO] Mesclando backup {ts} -> {DB_REDE}")
    _backup_rede()

    with sqlite3.connect(DB_REDE) as rede:
        rede.execute("PRAGMA foreign_keys = ON")
        _copiar_de_origem(bi, rede)
        _copiar_de_origem(bt, rede)
        rede.commit()

    print("[FIM] Mesclagem concluida. Abra a Auditoria e use Recarregar dados.")


if __name__ == "__main__":
    main()
