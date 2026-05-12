# Fluxo completo: encerra app nesta maquina -> backup pre-release -> build_release (PyInstaller + releases + current).
#
# Uso (na raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File tools\release_full.ps1
#   powershell -ExecutionPolicy Bypass -File tools\release_full.ps1 -IncludePythonMain
#   powershell -ExecutionPolicy Bypass -File tools\release_full.ps1 -SkipKill
#   powershell -ExecutionPolicy Bypass -File tools\release_full.ps1 -SkipCurrent
#
# -IncludePythonMain: tambem encerra python.exe rodando main.py / main_patrao.py desta pasta (dev).
# -SkipCurrent: build vai para releases/ mas NAO atualiza current/ (evita pedir pra colegas fecharem na hora).
# Outros PCs com o atalho em current: sem -SkipCurrent, robocopy pode falhar se alguem tiver o .exe aberto.

param(
    [switch]$SkipKill,
    [switch]$IncludePythonMain,
    [switch]$SkipCurrent
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

. (Join-Path $PSScriptRoot "close_local_sistema_pedidos.ps1")
if (-not $SkipKill) {
    Write-Host "[1/3] Encerrando processos locais (SistemaPedidosV2) ..."
    $null = Invoke-CloseLocalSistemaPedidos -ProjectRoot $Root -IncludePythonMain:$IncludePythonMain
    Start-Sleep -Seconds 1
}

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
$py = if (Test-Path $venvPy) { $venvPy } else { "python" }

Write-Host "[2/3] Backup pre-release (python) ..."
& $py (Join-Path $Root "tools\backup_pre_release.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/3] Build + release ..."
$br = Join-Path $PSScriptRoot "build_release.ps1"
$params = @("-ExecutionPolicy", "Bypass", "-File", $br)
if ($SkipKill) { $params += "-SkipKill" }
if ($IncludePythonMain) { $params += "-IncludePythonMain" }
if ($SkipCurrent) { $params += "-SkipCurrent" }
& powershell @params
exit $LASTEXITCODE
