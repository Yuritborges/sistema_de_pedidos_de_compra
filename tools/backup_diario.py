import os
import shutil
import sqlite3
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED


BASE_REDE = r"Z:\0 OBRAS\brasul_pedidos"
BASE_PROJETO = r"Z:\0 OBRAS\sistema_de_pedidos_brasulv2"

DB_FILES = {
    "iury": os.path.join(BASE_REDE, "Iury", "cotacao_iury.db"),
    "thamyres": os.path.join(BASE_REDE, "Thamyres", "cotacao_thamyres.db"),
    "rede": os.path.join(BASE_REDE, "cotacao_rede.db"),
}

CURRENT_DIR = os.path.join(BASE_PROJETO, "current")
BACKUP_ROOT = os.path.join(BASE_PROJETO, "backups")


def _agora():
    return datetime.now().strftime("%Y%m%d_%H%M")


def _sqlite_safe_backup(origem: str, destino: str):
    with sqlite3.connect(origem) as src, sqlite3.connect(destino) as dst:
        src.backup(dst)


def _backup_bancos(ts: str, pasta_saida: str):
    os.makedirs(pasta_saida, exist_ok=True)
    for nome, origem in DB_FILES.items():
        if not os.path.exists(origem):
            print(f"[AVISO] Banco não encontrado: {origem}")
            continue
        destino = os.path.join(pasta_saida, f"{nome}_{ts}.db")
        _sqlite_safe_backup(origem, destino)
        print(f"[OK] Backup banco: {destino}")


def _zip_current(ts: str, pasta_saida: str):
    if not os.path.exists(CURRENT_DIR):
        print(f"[AVISO] Pasta current não encontrada: {CURRENT_DIR}")
        return

    zip_path = os.path.join(pasta_saida, f"release_current_{ts}.zip")
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(CURRENT_DIR):
            for file_name in files:
                src = os.path.join(root, file_name)
                arc = os.path.relpath(src, os.path.dirname(CURRENT_DIR))
                zf.write(src, arc)
    print(f"[OK] Backup release: {zip_path}")


def _limpar_antigos(base: str, manter_dias: int = 30):
    limite = datetime.now().timestamp() - manter_dias * 86400
    for nome in os.listdir(base):
        caminho = os.path.join(base, nome)
        try:
            if os.path.isfile(caminho) and os.path.getmtime(caminho) < limite:
                os.remove(caminho)
        except Exception as exc:
            print(f"[AVISO] Falha ao limpar {caminho}: {exc}")


def main():
    ts = _agora()
    diaria_dir = os.path.join(BACKUP_ROOT, "diario")
    os.makedirs(diaria_dir, exist_ok=True)

    print(f"[INICIO] Backup diário {ts}")
    _backup_bancos(ts, diaria_dir)
    _zip_current(ts, diaria_dir)
    _limpar_antigos(diaria_dir, manter_dias=30)
    print(f"[FIM] Backup concluído em: {diaria_dir}")


if __name__ == "__main__":
    main()

