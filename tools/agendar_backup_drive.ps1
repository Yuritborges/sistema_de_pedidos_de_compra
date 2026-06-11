# Agenda backup diário no Google Drive — SEM janela de CMD.
# Rode como Administrador:
#   powershell -ExecutionPolicy Bypass -File tools\agendar_backup_drive.ps1
#
# Remove tarefas antigas de backup local (opcional) e registra a nova.

param(
    [string]$Hora = "18:30",
    [string]$TaskName = "BrasulPedidos_BackupDrive",
    [switch]$RemoverBackupAntigo
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Script = Join-Path $Root "backup_agendado.py"

if (-not (Test-Path $Script)) {
    throw "Nao encontrei: $Script"
}

$py = Join-Path $Root ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $py)) {
    $py = "pythonw.exe"
}

$Argument = "`"$Script`""

$Action = New-ScheduledTaskAction `
    -Execute $py `
    -Argument $Argument `
    -WorkingDirectory $Root

$Trigger = New-ScheduledTaskTrigger -Daily -At $Hora

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

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
    -Description "Backup cotacao_rede.db -> Google Drive (sem janela)." `
    -Force | Out-Null

Write-Host "OK Tarefa agendada: $TaskName"
Write-Host "   Horario: todo dia as $Hora"
Write-Host "   Script:  $Script (pythonw — sem CMD)"
Write-Host "   Log:     $Root\backup_agendado.log"
Write-Host ""

if ($RemoverBackupAntigo) {
    & (Join-Path $PSScriptRoot "desagendar_backup_diario.ps1")
}
