# Backup periódico dos bancos na rede (Iury, Thamyres, consolidado, locações).
# Usado pelo timer do app de pedidos; não substitui backup_diario.py (fim do dia com ZIP).

from __future__ import annotations

import os
import sqlite3
import time
from datetime import datetime

from app.data.cotacao_rede_sync import BASE_REDE, DB_IURY, DB_REDE, DB_THAMYRES

_PKG_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKUP_DIARIO_DIR = os.path.join(_PKG_ROOT, "backups", "diario")
BACKUP_ROLLING_DIR = os.path.join(BACKUP_DIARIO_DIR, "rolling")
_STAMP_PATH = os.path.join(BASE_REDE, ".ultimo_backup_periodico.txt")

DB_FILES = {
    "iury": DB_IURY,
    "thamyres": DB_THAMYRES,
    "rede": DB_REDE,
    "locacoes": os.path.join(BASE_REDE, "_shared", "locacoes.db"),
}


def _read_last_backup_ts() -> float:
    try:
        with open(_STAMP_PATH, encoding="utf-8") as f:
            return float(f.read().strip() or "0")
    except (OSError, ValueError):
        return 0.0


def _write_last_backup_ts(ts: float) -> None:
    try:
        os.makedirs(os.path.dirname(_STAMP_PATH), exist_ok=True)
        with open(_STAMP_PATH, "w", encoding="utf-8") as f:
            f.write(f"{ts:.3f}")
    except OSError:
        pass


def _sqlite_safe_backup(origem: str, destino: str) -> None:
    with sqlite3.connect(origem, timeout=15) as src, sqlite3.connect(destino) as dst:
        src.execute("PRAGMA busy_timeout = 15000")
        src.backup(dst)


def backup_bancos_rede_agora(silencioso: bool = True, rolling: bool = True) -> bool:
    """
    Cópia segura dos .db da rede.
    rolling=True (timer): sobrescreve backups/diario/rolling/*_latest.db (sem encher o disco).
    rolling=False: ficheiros com timestamp em backups/diario/ (uso manual / fim do dia).
    """
    os.makedirs(BACKUP_DIARIO_DIR, exist_ok=True)
    pasta = BACKUP_ROLLING_DIR if rolling else BACKUP_DIARIO_DIR
    os.makedirs(pasta, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    ok_any = False
    for nome, origem in DB_FILES.items():
        if not os.path.isfile(origem):
            continue
        if rolling:
            destino = os.path.join(pasta, f"{nome}_latest.db")
        else:
            destino = os.path.join(pasta, f"{nome}_{ts}.db")
        try:
            _sqlite_safe_backup(origem, destino)
            ok_any = True
            if not silencioso:
                print(f"[BACKUP] {destino}")
        except Exception as e:
            if not silencioso:
                print(f"[BACKUP] Falha {nome}: {e}")
    if ok_any:
        _write_last_backup_ts(time.time())
    return ok_any


def backup_bancos_rede_se_intervalo(intervalo_seg: int, silencioso: bool = True) -> bool:
    if intervalo_seg <= 0:
        return False
    agora = time.time()
    if agora - _read_last_backup_ts() < max(5, intervalo_seg - 3):
        return False
    return backup_bancos_rede_agora(silencioso=silencioso)
