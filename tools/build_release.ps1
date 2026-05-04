# Gera SistemaPedidosV2 com PyInstaller e copia para releases/ com carimbo de data.
# Uso (na raiz do projeto):  powershell -ExecutionPolicy Bypass -File tools\build_release.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$PyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $PyInstaller)) {
    throw "Nao encontrei $PyInstaller. Ative o .venv e instale: pip install pyinstaller"
}

Write-Host "[1/2] PyInstaller..."
& $PyInstaller (Join-Path $Root "SistemaPedidosV2.spec") --clean --noconfirm
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$src = Join-Path $Root "dist\SistemaPedidosV2"
$dest = Join-Path $Root "releases\SistemaPedidosV2_$stamp"

Write-Host "[2/2] Copiando para $dest ..."
New-Item -ItemType Directory -Path (Join-Path $Root "releases") -Force | Out-Null
Copy-Item -Path $src -Destination $dest -Recurse -Force

Write-Host "OK: $dest\SistemaPedidosV2.exe"
