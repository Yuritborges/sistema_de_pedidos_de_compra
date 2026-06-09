# services/backup_service.py
"""
Integração do backup local com o Google Drive.
Chamado após o backup local ser gerado com sucesso.
"""

import logging
from config.settings import Settings
from services.backup_drive_service import BackupDriveService  # ✅ Import correto agora

logger = logging.getLogger(__name__)


def executar_backup_com_nuvem(arquivos_gerados: list[str]) -> None:
    """
    Após o backup local, faz upload dos arquivos para o Google Drive.

    Args:
        arquivos_gerados: Lista de paths dos arquivos gerados pelo backup local
    """
    credentials_path = Settings.CREDENTIALS_DRIVE_PATH

    drive_service = BackupDriveService(
        credentials_path=credentials_path,
        folder_name="Brasul_Backups",
        folder_id="15o-YjEScb-IxtsgBNd6_ODAqi1NPvm0T"
    )

    resultado = drive_service.executar_backup_nuvem(arquivos_gerados)

    # Log do resultado
    if resultado["falha"] == 0:
        logger.info(f"Backup na nuvem: {resultado['sucesso']} arquivo(s) enviado(s) com sucesso")
    else:
        logger.warning(
            f"Backup nuvem parcial: {resultado['sucesso']} OK, "
            f"{resultado['falha']} falha(s)"
        )
        for erro in resultado["erros"]:
            logger.error(f"  → {erro}")
