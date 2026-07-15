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

# Mapeamento novo (2026-07): a unidade pode apontar direto para "0 obras",
# deixando o atalho na raiz ({letra}:\). Mantem compatibilidade com o layout
# antigo ({letra}:\0 OBRAS) e com o caminho UNC.
$pastasCandidatas = @()
foreach ($letra in "ZYXWVUTSRQPONMLKJIHGFED".ToCharArray()) {
    $pastasCandidatas += "${letra}:\"
    $pastasCandidatas += "${letra}:\0 OBRAS"
}
$pastasCandidatas += "\\192.168.15.250\arquivos brasul\0 obras"

$lnk = $null
foreach ($pasta in $pastasCandidatas) {
    if (-not (Test-Path $pasta)) { continue }
    $cand = Join-Path $pasta "$NomeAtalho.lnk"
    if (Test-Path $cand) { $lnk = $cand; break }
}
if (-not $lnk) {
    throw "Atalho '$NomeAtalho.lnk' nao encontrado (raiz da unidade, 0 OBRAS ou UNC)."
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
