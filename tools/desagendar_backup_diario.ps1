# Remove tarefas antigas de backup local que abriam janela de CMD ao ligar o PC.
# Rode como Administrador:
#   powershell -ExecutionPolicy Bypass -File tools\desagendar_backup_diario.ps1

$ErrorActionPreference = "SilentlyContinue"

$nomes = @(
    "BrasulPedidos_BackupDiario",
    "Brasul_BackupDiario_Pedidos",
    "Brasul Backup Diario",
    "BackupDiarioBrasul"
)

Write-Host "Removendo tarefas antigas de backup local..."
foreach ($nome in $nomes) {
    $t = Get-ScheduledTask -TaskName $nome -ErrorAction SilentlyContinue
    if ($t) {
        Unregister-ScheduledTask -TaskName $nome -Confirm:$false
        Write-Host "  [OK] Removida: $nome"
    }
}

Write-Host ""
Write-Host "Se ainda abrir CMD ao ligar o PC, verifique no Agendador de Tarefas:"
Write-Host "  - Pasta Inicializar (Startup)"
Write-Host "  - BACKUP_DIARIO.bat na pasta do projeto na rede"
Write-Host ""
Write-Host "Backup atual: tools\agendar_backup_drive.ps1 -> backup_agendado.py (Google Drive)"
