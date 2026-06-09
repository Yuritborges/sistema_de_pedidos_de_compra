# services/backup_drive_service.py
"""
Serviço de upload de backups para o Google Drive.
Usa OAuth2 com conta do usuário — requer token.json gerado previamente.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# Escopos — deve ser igual ao usado ao gerar o token
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Caminhos dos arquivos de autenticação (na pasta do projeto na rede)
CREDENTIALS_PATH = Path(__file__).parent.parent / "credentials_oauth.json"
TOKEN_PATH = Path(__file__).parent.parent / "token.json"

# ID da pasta no Google Drive onde os backups serão salvos
# Como obter: abra a pasta no Drive, o ID é o trecho final da URL
# Ex: https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOp  →  ID = 1AbCdEfGhIjKlMnOp
DRIVE_FOLDER_ID = "SEU_FOLDER_ID_AQUI"


def _obter_credenciais() -> Optional[Credentials]:
    """
    Carrega e valida as credenciais OAuth2 do token.json.
    Renova automaticamente se o token estiver expirado.

    Returns:
        Credentials válidas ou None em caso de falha.
    """
    if not TOKEN_PATH.exists():
        logger.error(
            "token.json não encontrado em %s. "
            "Execute utils/gerar_token_drive.py no seu PC primeiro.",
            TOKEN_PATH
        )
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

        # Renova automaticamente se expirado (usa o refresh_token)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                logger.info("Token expirado — renovando automaticamente...")
                creds.refresh(Request())
                # Salva o token renovado para a próxima vez
                TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
                logger.info("Token renovado e salvo com sucesso.")
            else:
                logger.error("Token inválido e sem refresh_token. Gere um novo token.")
                return None

        return creds

    except Exception as e:
        logger.error("Erro ao carregar credenciais OAuth2: %s", e)
        return None


def fazer_upload_backup(caminho_arquivo: Path) -> bool:
    """
    Faz upload de um arquivo de backup para o Google Drive.

    Args:
        caminho_arquivo: Caminho local do arquivo a ser enviado.

    Returns:
        True se o upload foi bem-sucedido, False caso contrário.
    """
    if not caminho_arquivo.exists():
        logger.error("Arquivo de backup não encontrado: %s", caminho_arquivo)
        return False

    creds = _obter_credenciais()
    if not creds:
        return False

    try:
        # Conecta à API do Drive
        service = build("drive", "v3", credentials=creds)

        # Nome do arquivo no Drive inclui timestamp para não sobrescrever
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_no_drive = f"backup_{timestamp}_{caminho_arquivo.name}"

        # Metadados do arquivo
        file_metadata = {
            "name": nome_no_drive,
            "parents": [DRIVE_FOLDER_ID],
        }

        # Prepara o upload
        media = MediaFileUpload(
            str(caminho_arquivo),
            mimetype="application/octet-stream",
            resumable=True  # Permite retomar uploads interrompidos
        )

        logger.info("Iniciando upload: %s → Google Drive...", caminho_arquivo.name)

        # Executa o upload
        arquivo_criado = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, size",
            )
            .execute()
        )

        logger.info(
            "✅ Upload concluído! Arquivo: %s | ID: %s | Tamanho: %s bytes",
            arquivo_criado.get("name"),
            arquivo_criado.get("id"),
            arquivo_criado.get("size"),
        )
        return True

    except Exception as e:
        logger.error("❌ Erro no upload para o Google Drive: %s", e)
        return False
