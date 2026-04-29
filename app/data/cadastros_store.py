import os
import shutil


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_ASSETS_DIR = os.path.join(BASE_DIR, "assets")

LOCAL_FORNECEDORES = os.path.join(LOCAL_ASSETS_DIR, "fornecedores.json")
LOCAL_OBRAS = os.path.join(LOCAL_ASSETS_DIR, "obras.json")
LOCAL_FUNCIONARIOS = os.path.join(LOCAL_ASSETS_DIR, "funcionarios.json")

try:
    from config import REDE_BASE_DIR
except Exception:
    REDE_BASE_DIR = os.path.join(BASE_DIR, "database")

CADASTROS_DIR = os.path.join(REDE_BASE_DIR, "cadastros_compartilhados")
FORNECEDORES_JSON = os.path.join(CADASTROS_DIR, "fornecedores.json")
OBRAS_JSON = os.path.join(CADASTROS_DIR, "obras.json")
FUNCIONARIOS_JSON = os.path.join(CADASTROS_DIR, "funcionarios.json")


def _seed_if_missing(shared_path: str, local_path: str, default_content: str):
    if os.path.exists(shared_path):
        return

    os.makedirs(os.path.dirname(shared_path), exist_ok=True)

    if os.path.exists(local_path):
        shutil.copy2(local_path, shared_path)
        return

    with open(shared_path, "w", encoding="utf-8") as f:
        f.write(default_content)


def ensure_cadastros_storage():
    _seed_if_missing(FORNECEDORES_JSON, LOCAL_FORNECEDORES, "{}")
    _seed_if_missing(OBRAS_JSON, LOCAL_OBRAS, "{}")
    _seed_if_missing(FUNCIONARIOS_JSON, LOCAL_FUNCIONARIOS, "[]")


ensure_cadastros_storage()

