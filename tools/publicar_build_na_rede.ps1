# Publica um build já gerado em current\ na pasta de rede (Z:\...).
# Pode rodar em QUALQUER PC com a unidade Z: mapeada — não precisa ser a máquina de dev.
#
# Origem (escolha uma):
#   A) dist\SistemaPedidosV2\  (build local)
#   B) pasta extraída do zip baixado do GitHub Actions / Release
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1
#   powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "D:\Downloads\SistemaPedidosV2"
#   powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -SkipKill

param(
    [string]$Origem = "",
    [switch]$SkipKill
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if (-not $Origem) {
    $Origem = Join-Path $Root "dist\SistemaPedidosV2"
}
$Origem = (Resolve-Path $Origem -ErrorAction Stop).Path
$exe = Join-Path $Origem "SistemaPedidosV2.exe"
if (-not (Test-Path $exe)) {
    throw "Nao encontrei $exe. Extraia o zip do GitHub ou rode build_release.ps1 antes."
}

$cur = Join-Path $Root "current"
$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$destRelease = Join-Path $Root "releases\SistemaPedidosV2_$stamp"

Write-Host "[1/3] Snapshot em releases\$($stamp) ..."
New-Item -ItemType Directory -Path $destRelease -Force | Out-Null
Copy-Item -Path $Origem\* -Destination $destRelease -Recurse -Force

. (Join-Path $PSScriptRoot "close_local_sistema_pedidos.ps1")
if (-not $SkipKill) {
    Write-Host "[2/3] Encerrando SistemaPedidosV2 neste PC ..."
    $null = Invoke-CloseLocalSistemaPedidos -ProjectRoot $Root
    Start-Sleep -Seconds 1
}

Write-Host "[3/3] Atualizando current\ (atalhos da rede) ..."
New-Item -ItemType Directory -Path $cur -Force | Out-Null
. (Join-Path $PSScriptRoot "robocopy_mirror.ps1")
$rc = Invoke-RobocopyMirror -Source $Origem -Destination $cur
if ($rc -ge 8) {
    throw "Falha ao copiar para current (robocopy $rc). Feche o .exe em todos os PCs e tente de novo."
}

Write-Host "OK current: $cur\SistemaPedidosV2.exe"
Write-Host "OK releases: $destRelease\SistemaPedidosV2.exe"
