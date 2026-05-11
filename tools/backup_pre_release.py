"""
Backup antes de release: fonte (zip) + bancos locais e da rede (pedidos atuais).

Uso na raiz do projeto:
  set PYTHONUNBUFFERED=1
  python tools/backup_pre_release.py
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
BACKUP_ROOT = ROOT / "backups"


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")


def _sqlite_backup(origem: Path, destino: Path) -> bool:
    if not origem.is_file():
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(origem) as src, sqlite3.connect(destino) as dst:
        src.backup(dst)
    return True


def _zip_fonte(out: Path) -> None:
    with ZipFile(out, "w", compression=ZIP_DEFLATED) as zf:
        for name in (
            "main.py",
            "config.py",
            "config_exemplo.py",
            "requirements.txt",
            "README.md",
            "SistemaPedidosV2.spec",
            "Brasul-Pedidos.spec",
            "main.spec",
        ):
            p = ROOT / name
            if p.is_file():
                zf.write(p, name)
        if (ROOT / "app").is_dir():
            for p in (ROOT / "app").rglob("*"):
                if p.is_file() and "__pycache__" not in p.parts:
                    zf.write(p, f"app/{p.relative_to(ROOT / 'app').as_posix()}")
        tdir = ROOT / "tools"
        if tdir.is_dir():
            for p in tdir.rglob("*.py"):
                if "__pycache__" not in p.parts:
                    zf.write(p, f"tools/{p.relative_to(tdir).as_posix()}")
            for name in ("build_release.ps1", "robocopy_mirror.ps1", "sync_current_from_dist.ps1"):
                p = tdir / name
                if p.is_file():
                    zf.write(p, f"tools/{name}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    ts = _ts()
    pasta = BACKUP_ROOT / f"pre_release_{ts}"
    pasta.mkdir(parents=True, exist_ok=True)
    print(f"[INICIO] Backup pre-release -> {pasta}", flush=True)

    zip_fonte = pasta / f"fonte_{ts}.zip"
    _zip_fonte(zip_fonte)
    print(f"[OK] Zip fonte: {zip_fonte}", flush=True)

    try:
        sys.path.insert(0, str(ROOT))
        import config as cfg  # noqa: E402

        db = Path(getattr(cfg, "DATABASE_PATH", "") or "")
        if db.is_file():
            dest = pasta / f"local_{db.name.replace('.db', '')}_{ts}.db"
            if _sqlite_backup(db, dest):
                print(f"[OK] Banco local: {dest}", flush=True)
        bd = Path(getattr(cfg, "BACKUP_DIR", "") or "")
        if bd.is_dir():
            snap = pasta / "backup_dir_cotacao"
            shutil.copytree(bd, snap, dirs_exist_ok=True)
            print(f"[OK] Copia pasta backup DB: {snap}", flush=True)
    except Exception as e:
        print(f"[AVISO] Banco local/config: {e}", flush=True)

    rede = Path(r"Z:\0 OBRAS\brasul_pedidos")
    pares = [
        ("iury", rede / "Iury" / "cotacao_iury.db"),
        ("thamyres", rede / "Thamyres" / "cotacao_thamyres.db"),
        ("rede", rede / "cotacao_rede.db"),
        ("locacoes", rede / "_shared" / "locacoes.db"),
    ]
    for label, orig in pares:
        if orig.is_file():
            dest = pasta / f"{label}_{ts}.db"
            if _sqlite_backup(orig, dest):
                print(f"[OK] Banco rede {label}: {dest}", flush=True)

    cad = rede / "cadastros_compartilhados"
    if cad.is_dir():
        destc = pasta / "cadastros_compartilhados"
        shutil.copytree(cad, destc, dirs_exist_ok=True)
        print(f"[OK] Cadastros rede: {destc}", flush=True)

    if os.environ.get("BACKUP_INCLUDE_CURRENT") == "1":
        cur = ROOT / "current"
        if cur.is_dir() and any(cur.iterdir()):
            snapc = pasta / "current_snapshot"
            shutil.copytree(cur, snapc, dirs_exist_ok=True)
            print(f"[OK] Snapshot current/: {snapc}", flush=True)

    print(f"[FIM] Backup concluido: {pasta}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
