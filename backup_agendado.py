# backup_agendado.py
"""
Script independente de backup diário.
Copia o cotacao_rede.db para o Google Drive.
Executado pelo Agendador de Tarefas do Windows às 18:30.
NÃO depende do programa estar aberto.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ─── Configurações ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

BANCO_ORIGEM        = Path(r"Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db")  # ✅ caminho real do banco
PASTA_BACKUP_LOCAL  = Path(r"Z:\0 OBRAS\brasul_pedidos\BACKUPS")          # ✅ backup local junto ao banco
TOKEN_PATH          = BASE_DIR / "app" / "config" / "token.json"          # ✅ token no lugar certo
DRIVE_FOLDER_ID     = "15o-YjEScb-IxtsgBNd6_ODAqi1NPvm0T"
SCOPES              = ["https://www.googleapis.com/auth/drive"]


# ─── Log ──────────────────────────────────────────────────────────
LOG_PATH = Path(__file__).parent / "backup_agendado.log"
logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)


def obter_credenciais() -> Credentials | None:
    """Carrega e renova o token OAuth2 se necessário."""
    if not TOKEN_PATH.exists():
        logger.error("token.json não encontrado em: %s", TOKEN_PATH)
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
                logger.info("Token renovado com sucesso.")
            else:
                logger.error("Token inválido. Gere um novo token.")
                return None
        return creds
    except Exception as e:
        logger.error("Erro ao carregar credenciais: %s", e)
        return None


def fazer_backup() -> None:
    """Fluxo principal: copia local + envia pro Drive."""
    logger.info("=" * 50)
    logger.info("Iniciando backup diário...")

    # 1. Verifica se o banco existe
    if not BANCO_ORIGEM.exists():
        logger.error("Banco não encontrado: %s", BANCO_ORIGEM)
        return

    # 2. Copia localmente com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"cotacao_rede_{timestamp}.db"
    PASTA_BACKUP_LOCAL.mkdir(parents=True, exist_ok=True)
    destino_local = PASTA_BACKUP_LOCAL / nome_backup
    shutil.copy2(BANCO_ORIGEM, destino_local)
    logger.info("Backup local criado: %s", destino_local)

    # 3. Upload para o Google Drive
    creds = obter_credenciais()
    if not creds:
        logger.error("Backup local ok, mas upload cancelado (sem credenciais).")
        return

    try:
        service = build("drive", "v3", credentials=creds)
        media = MediaFileUpload(
            str(destino_local),
            mimetype="application/octet-stream",
            resumable=True
        )
        arquivo = service.files().create(
            body={"name": nome_backup, "parents": [DRIVE_FOLDER_ID]},
            media_body=media,
            fields="id, name"
        ).execute()
        logger.info("✅ Upload concluído! Arquivo no Drive: %s (ID: %s)",
                    arquivo.get("name"), arquivo.get("id"))
    except Exception as e:
        logger.error("❌ Erro no upload pro Drive: %s", e)

    logger.info("Backup finalizado.")


if __name__ == "__main__":
    fazer_backup()
