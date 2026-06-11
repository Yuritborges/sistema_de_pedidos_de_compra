# [DESCONTINUADO] Backup local antigo — substituído por Google Drive.
# Use:  tools\agendar_backup_drive.ps1
# Remova tarefa antiga:  tools\desagendar_backup_diario.ps1
#
# Este script permanece só para referência. Não agende mais backup_diario.py.

param(
    [string]$Hora = "08:08",
    [string]$TaskName = "BrasulPedidos_BackupDiario"
)

Write-Host "AVISO: backup_diario local foi substituido por backup_agendado.py (Google Drive)."
Write-Host "Execute: powershell -ExecutionPolicy Bypass -File tools\desagendar_backup_diario.ps1"
Write-Host "Depois:  powershell -ExecutionPolicy Bypass -File tools\agendar_backup_drive.ps1 -RemoverBackupAntigo"
exit 1

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Vbs = Join-Path $Root "tools\run_backup_diario_silencioso.vbs"

if (-not (Test-Path $Vbs)) {
    throw "Nao encontrei: $Vbs"
}

$Action = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "//B `"$Vbs`"" `
    -WorkingDirectory $Root

$Trigger = New-ScheduledTaskTrigger -Daily -At $Hora

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Backup diario Brasul Pedidos (bancos, cadastros, current) — sem janela." `
    -Force | Out-Null

Write-Host "OK Tarefa agendada: $TaskName"
Write-Host "   Horario: todo dia as $Hora"
Write-Host "   Script:  $Vbs"
Write-Host "   Logs:    $Root\backups\diario\logs\"
Write-Host ""
Write-Host "Se existia tarefa antiga abrindo cmd.exe, desative-a no Agendador de Tarefas."
