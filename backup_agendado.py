# backup_agendado.py
"""
Backup diário do banco consolidado → cópia local + Google Drive.
Executado pelo Agendador de Tarefas do Windows (tools/agendar_backup_drive.ps1).
NÃO depende do programa de pedidos estar aberto.
"""

from __future__ import annotations

import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Garante imports do projeto quando rodado pelo Agendador de Tarefas
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config.settings import (
    DRIVE_BACKUP_LOG_PATH,
    DRIVE_BANCO_ORIGEM,
    DRIVE_FOLDER_ID,
    DRIVE_PASTA_BACKUP_LOCAL,
    TOKEN_DRIVE_PATH,
)

SCOPES = ["https://www.googleapis.com/auth/drive"]

BANCO_ORIGEM = Path(DRIVE_BANCO_ORIGEM)
PASTA_BACKUP_LOCAL = Path(DRIVE_PASTA_BACKUP_LOCAL)
TOKEN_PATH = Path(TOKEN_DRIVE_PATH)
LOG_PATH = Path(DRIVE_BACKUP_LOG_PATH)


def _configurar_log() -> logging.Logger:
    """Configura log em arquivo (sem janela de CMD)."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_PATH),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        encoding="utf-8",
        force=True,
    )
    return logging.getLogger(__name__)


logger = _configurar_log()


def obter_credenciais() -> Credentials | None:
    """Carrega e renova o token OAuth2 se necessário."""
    if not TOKEN_PATH.is_file():
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
                logger.error("Token inválido. Execute tools/gerar_token_drive.py.")
                return None
        return creds
    except Exception as exc:
        logger.error("Erro ao carregar credenciais: %s", exc)
        return None


def fazer_backup() -> None:
    """Copia cotacao_rede.db localmente e envia para o Google Drive."""
    logger.info("=" * 50)
    logger.info("Iniciando backup diário (Google Drive)...")

    if not BANCO_ORIGEM.is_file():
        logger.error("Banco não encontrado: %s", BANCO_ORIGEM)
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"cotacao_rede_{timestamp}.db"
    PASTA_BACKUP_LOCAL.mkdir(parents=True, exist_ok=True)
    destino_local = PASTA_BACKUP_LOCAL / nome_backup

    try:
        shutil.copy2(BANCO_ORIGEM, destino_local)
        logger.info("Backup local criado: %s", destino_local)
    except OSError as exc:
        logger.error("Falha na cópia local: %s", exc)
        return

    creds = obter_credenciais()
    if not creds:
        logger.error("Upload cancelado (sem credenciais válidas).")
        return

    try:
        service = build("drive", "v3", credentials=creds)
        media = MediaFileUpload(
            str(destino_local),
            mimetype="application/octet-stream",
            resumable=True,
        )
        arquivo = service.files().create(
            body={"name": nome_backup, "parents": [DRIVE_FOLDER_ID]},
            media_body=media,
            fields="id, name",
        ).execute()
        logger.info(
            "Upload concluído: %s (ID: %s)",
            arquivo.get("name"),
            arquivo.get("id"),
        )
    except Exception as exc:
        logger.error("Erro no upload para o Drive: %s", exc)

    logger.info("Backup finalizado.")


if __name__ == "__main__":
    fazer_backup()
