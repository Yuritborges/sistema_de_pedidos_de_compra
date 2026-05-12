# Gera SistemaPedidosV2 com PyInstaller, copia para releases/ (com data) e para current/
# (atalho fixo: ...\sistema_de_pedidos_brasulv2\current\SistemaPedidosV2.exe).
#
# Uso (na raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
#   powershell -ExecutionPolicy Bypass -File tools\build_release.ps1 -SkipKill
#   powershell -ExecutionPolicy Bypass -File tools\build_release.ps1 -IncludePythonMain
#   powershell -ExecutionPolicy Bypass -File tools\build_release.ps1 -SkipCurrent
#
# Por padrao encerra SistemaPedidosV2.exe NESTA MAQUINA antes do build e antes do robocopy em current/.
# -SkipCurrent: gera dist + releases com data, NAO espelha em current/ (ninguem precisa fechar o atalho
#   na hora; depois rode tools\sync_current_from_dist.ps1 quando todos fecharem o .exe).
# Outros PCs na rede: sem -SkipCurrent, robocopy em current/ falha se alguem tiver o .exe aberto la.

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
    Write-Host "[0/4] Encerrando app local (liberar arquivos) ..."
    $null = Invoke-CloseLocalSistemaPedidos -ProjectRoot $Root -IncludePythonMain:$IncludePythonMain
}

$PyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $PyInstaller)) {
    throw "Nao encontrei $PyInstaller. Ative o .venv e instale: pip install pyinstaller"
}

Write-Host "[1/4] PyInstaller..."
& $PyInstaller (Join-Path $Root "SistemaPedidosV2.spec") --clean --noconfirm
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$src = Join-Path $Root "dist\SistemaPedidosV2"
if (-not (Test-Path (Join-Path $src "SistemaPedidosV2.exe"))) {
    throw "Build incompleto: nao achei $src\SistemaPedidosV2.exe."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$destRelease = Join-Path $Root "releases\SistemaPedidosV2_$stamp"

Write-Host "[2/4] Copiando para $destRelease ..."
New-Item -ItemType Directory -Path (Join-Path $Root "releases") -Force | Out-Null
Copy-Item -Path $src -Destination $destRelease -Recurse -Force

if (-not $SkipCurrent) {
    if (-not $SkipKill) {
        Write-Host "[3/4] Encerrando app local de novo antes de current/ ..."
        $null = Invoke-CloseLocalSistemaPedidos -ProjectRoot $Root -IncludePythonMain:$IncludePythonMain
        Start-Sleep -Seconds 1
    }

    Write-Host "[4/4] Atualizando pasta current (atalhos da rede) ..."
    $cur = Join-Path $Root "current"
    New-Item -ItemType Directory -Path $cur -Force | Out-Null
    . (Join-Path $PSScriptRoot "robocopy_mirror.ps1")
    $rc = Invoke-RobocopyMirror -Source $src -Destination $cur
    if ($rc -ge 8) {
        throw "Falha ao copiar para current (robocopy codigo $rc). Feche o SistemaPedidosV2 em todos os PCs e rode: tools\sync_current_from_dist.ps1"
    }
}

Write-Host "OK releases: $destRelease\SistemaPedidosV2.exe"
if (-not $SkipCurrent) {
    $cur = Join-Path $Root "current"
    Write-Host "OK current:  $cur\SistemaPedidosV2.exe"
    Write-Host "Quem usa o atalho em current recebe esta versao na proxima abertura."
}
else {
    Write-Host "Pulado current/. Quando todos fecharem o programa: tools\sync_current_from_dist.ps1"
}
