# Registra backup diário OCULTO no Agendador de Tarefas do Windows.
# Rode como Administrador (botão direito PowerShell -> Executar como administrador):
#   powershell -ExecutionPolicy Bypass -File tools\agendar_backup_diario.ps1
#
# Para remover: Unregister-ScheduledTask -TaskName "BrasulPedidos_BackupDiario" -Confirm:$false

param(
    [string]$Hora = "08:08",
    [string]$TaskName = "BrasulPedidos_BackupDiario"
)

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
