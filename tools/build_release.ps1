# Gera SistemaPedidosV2 com PyInstaller, copia para releases/ (com data) e para current/
# (atalho fixo: ...\sistema_de_pedidos_brasulv2\current\SistemaPedidosV2.exe).
#
# Uso (na raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
#
# Dica: feche o programa em todos os PCs antes de rodar, para nao travar arquivos em uso.

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$PyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $PyInstaller)) {
    throw "Nao encontrei $PyInstaller. Ative o .venv e instale: pip install pyinstaller"
}

Write-Host "[1/3] PyInstaller..."
& $PyInstaller (Join-Path $Root "SistemaPedidosV2.spec") --clean --noconfirm
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$src = Join-Path $Root "dist\SistemaPedidosV2"
if (-not (Test-Path (Join-Path $src "SistemaPedidosV2.exe"))) {
    throw "Build incompleto: nao achei $src\SistemaPedidosV2.exe."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$destRelease = Join-Path $Root "releases\SistemaPedidosV2_$stamp"

Write-Host "[2/3] Copiando para $destRelease ..."
New-Item -ItemType Directory -Path (Join-Path $Root "releases") -Force | Out-Null
Copy-Item -Path $src -Destination $destRelease -Recurse -Force

Write-Host "[3/3] Atualizando pasta current (atalhos da rede) ..."
$cur = Join-Path $Root "current"
New-Item -ItemType Directory -Path $cur -Force | Out-Null
# /MIR espelha; /R /W = retentativas (arquivos em uso = feche o SistemaPedidosV2 em todos os PCs)
$rc = (Start-Process -FilePath "robocopy.exe" -ArgumentList @(
    $src, $cur, "/MIR", "/R:30", "/W:3", "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
) -Wait -PassThru).ExitCode
if ($rc -ge 8) {
    throw "Falha ao copiar para current (robocopy codigo $rc). Feche o SistemaPedidosV2 em todos os PCs e rode: tools\sync_current_from_dist.ps1"
}

Write-Host "OK releases: $destRelease\SistemaPedidosV2.exe"
Write-Host "OK current:  $cur\SistemaPedidosV2.exe"
Write-Host "Quem usa o atalho em current recebe esta versao na proxima abertura."
