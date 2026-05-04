# Copia dist\SistemaPedidosV2 para current\ (sem rodar PyInstaller).
# Usa robocopy /MIR para nao depender de apagar a pasta inteira (menos conflito com arquivos em uso).
# Se ainda falhar, feche o SistemaPedidosV2 em todos os PCs e rode de novo.
#
# Uso: powershell -ExecutionPolicy Bypass -File tools\sync_current_from_dist.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$src = Join-Path $Root "dist\SistemaPedidosV2"
$cur = Join-Path $Root "current"

if (-not (Test-Path (Join-Path $src "SistemaPedidosV2.exe"))) {
    throw "Nao encontrei $src\SistemaPedidosV2.exe. Rode build_release.ps1 antes."
}
New-Item -ItemType Directory -Path $cur -Force | Out-Null

# /MIR espelha dest para ficar igual ao dist; codigos 0-7 = OK no robocopy
$rc = (Start-Process -FilePath "robocopy.exe" -ArgumentList @(
    $src, $cur, "/MIR", "/R:30", "/W:3", "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
) -Wait -PassThru).ExitCode
if ($rc -ge 8) {
    throw "robocopy falhou (codigo $rc). Feche o SistemaPedidosV2 e tente de novo."
}
Write-Host "OK: $cur\SistemaPedidosV2.exe"
