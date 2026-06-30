# Atualiza o atalho EXISTENTE em 0 OBRAS (icone embutido no .exe, sem arquivos novos na pasta).
#
#   powershell -ExecutionPolicy Bypass -File tools\atualizar_atalho_pedidos_rede.ps1

param(
    [string]$NomeAtalho = "SISTEMA DE PEDIDOS DE COMPRAS BRASUL"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent

function Convert-PathToUnc {
    param([string]$Path)
    if (-not $Path) { return $Path }
    $resolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    if ($resolved -match '^\\\\') { return $resolved }
    if ($resolved -match '^([A-Za-z]):\\') {
        $letra = $Matches[1]
        $psDrive = Get-PSDrive -Name $letra -ErrorAction SilentlyContinue
        $uncRoot = ($psDrive.DisplayRoot -as [string]).TrimEnd('\')
        if ($uncRoot -and $uncRoot -match '^\\\\') {
            return $uncRoot + $resolved.Substring(2)
        }
    }
    return $resolved
}

$exe = Join-Path $Root "current\SistemaPedidosV2.exe"
if (-not (Test-Path $exe)) {
    throw "Nao encontrei $exe. Rode build_release.ps1 antes."
}

$obras = $null
foreach ($letra in "ZYXWVUTSRQPONMLKJIHGFED") {
    $p = "${letra}:\0 OBRAS"
    if (Test-Path $p) { $obras = $p; break }
}
if (-not $obras) {
    $obras = "\\192.168.15.250\arquivos brasul\0 OBRAS"
}
if (-not (Test-Path $obras)) {
    throw "Pasta 0 OBRAS nao encontrada."
}

$lnk = Join-Path $obras "$NomeAtalho.lnk"
if (-not (Test-Path $lnk)) {
    throw "Atalho nao encontrado: $lnk"
}

$exeUnc = Convert-PathToUnc $exe
$workUnc = Convert-PathToUnc (Split-Path $exe -Parent)

$Wsh = New-Object -ComObject WScript.Shell
$sc = $Wsh.CreateShortcut($lnk)
$sc.TargetPath = $exeUnc
$sc.WorkingDirectory = $workUnc
$sc.IconLocation = "$exeUnc,0"
$sc.Description = "Sistema de Pedidos - Brasul Construtora"
$sc.Save()

Write-Host "Atalho atualizado: $lnk"
Write-Host "  Destino: $($sc.TargetPath)"
Write-Host "  Icone:   $($sc.IconLocation) (embutido no exe)"
