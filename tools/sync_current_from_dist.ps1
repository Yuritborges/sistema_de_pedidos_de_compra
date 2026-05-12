# Copia dist\SistemaPedidosV2 para current\ (sem rodar PyInstaller).
# Caminhos com espacos (ex.: Z:\0 OBRAS\...) sao tratados corretamente.
#
# Uso (na raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File tools\sync_current_from_dist.ps1
#   powershell -ExecutionPolicy Bypass -File tools\sync_current_from_dist.ps1 -SkipKill

param(
    [switch]$SkipKill,
    [switch]$IncludePythonMain
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
$src = Join-Path $Root "dist\SistemaPedidosV2"
$cur = Join-Path $Root "current"

if (-not (Test-Path (Join-Path $src "SistemaPedidosV2.exe"))) {
    throw "Nao encontrei $src\SistemaPedidosV2.exe. Rode build_release.ps1 ou pyinstaller antes."
}
New-Item -ItemType Directory -Path $cur -Force | Out-Null

. (Join-Path $PSScriptRoot "close_local_sistema_pedidos.ps1")
if (-not $SkipKill) {
    Write-Host "Encerrando app local antes do robocopy ..."
    $null = Invoke-CloseLocalSistemaPedidos -ProjectRoot $Root -IncludePythonMain:$IncludePythonMain
    Start-Sleep -Seconds 1
}

. (Join-Path $PSScriptRoot "robocopy_mirror.ps1")
$rc = Invoke-RobocopyMirror -Source $src -Destination $cur

# Robocopy: 0-7 = operacao concluida (bits combinados); >= 8 falha
if ($rc -ge 8) {
    $msg = @()
    $msg += "robocopy falhou (codigo $rc)."
    if ($rc -eq 16) {
        $msg += "Codigo 16 = erro grave (caminho invalido, permissao, ou sintaxe)."
        $msg += "Confira se existe: $src"
        $msg += "Feche SistemaPedidosV2 em todos os PCs se for arquivo em uso."
    } else {
        $msg += "Feche SistemaPedidosV2 em todos os PCs e tente de novo."
    }
    throw ($msg -join " ")
}

Write-Host "OK: $cur\SistemaPedidosV2.exe"
