# Recria os atalhos em Z:\0 OBRAS com caminhos UNC (funciona com Z:, Y: ou sem letra).
# Copia icones na mesma pasta do .lnk.
#
#   powershell -ExecutionPolicy Bypass -File tools\corrigir_atalhos_rede_obras.ps1

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

function Get-IconeOrigemBrasul {
    $candidatos = @(
        (Join-Path $Root "assets\iconebrasul2.ico"),
        (Join-Path $Root "assets\logos\logo_brasul.ico"),
        (Join-Path $Root "assets\logo.ico"),
        (Join-Path $Root "current\SistemaPedidosV2.ico")
    )
    foreach ($p in $candidatos) {
        if (Test-Path $p) { return $p }
    }
    throw "Nenhum .ico encontrado para Brasul."
}

function Publish-IconeCopia {
    param([string]$Pasta, [string]$Nome)
    $origem = Get-IconeOrigemBrasul
    $dest = Join-Path $Pasta $Nome
    Copy-Item $origem $dest -Force
    Write-Host "  Icone: $dest"
    return $dest
}

function New-AtalhoUnc {
    param(
        [string]$Lnk,
        [string]$Exe,
        [string]$Icon,
        [string]$Descricao = ""
    )
    if (-not (Test-Path $Exe)) {
        Write-Host "  [PULADO] Exe nao encontrado: $Exe"
        return
    }
    $Wsh = New-Object -ComObject WScript.Shell
    $sc = $Wsh.CreateShortcut($Lnk)
    $sc.TargetPath = Convert-PathToUnc $Exe
    $sc.WorkingDirectory = Convert-PathToUnc (Split-Path $Exe -Parent)
    if ($Icon -and (Test-Path $Icon)) {
        $sc.IconLocation = "$(Convert-PathToUnc $Icon),0"
    } elseif (Test-Path $Exe) {
        $sc.IconLocation = "$(Convert-PathToUnc $Exe),0"
    }
    if ($Descricao) { $sc.Description = $Descricao }
    $sc.Save()
    Write-Host "  Atalho: $Lnk"
    Write-Host "    -> $($sc.TargetPath)"
    Write-Host "    icone $($sc.IconLocation)"
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

Write-Host "Pasta atalhos: $obras"
Write-Host ""

Write-Host "[1/3] SISTEMA DE PEDIDOS DE COMPRAS BRASUL ..."
$exePed = Join-Path $Root "current\SistemaPedidosV2.exe"
Publish-IconeCopia -Pasta (Join-Path $Root "current") -Nome "SistemaPedidosV2.ico" | Out-Null
New-AtalhoUnc `
    -Lnk (Join-Path $obras "SISTEMA DE PEDIDOS DE COMPRAS BRASUL.lnk") `
    -Exe $exePed `
    -Icon $exePed `
    -Descricao "Sistema de Pedidos - Brasul Construtora"

Write-Host ""
Write-Host "[2/3] SISTEMA DE BUSCA DE ATESTADOS BRASUL ..."
$exeAtest = Join-Path $obras "Sistema_de_atestado_brasul\current\Cofre_Brasul.exe"
New-AtalhoUnc `
    -Lnk (Join-Path $obras "SISTEMA DE BUSCA DE ATESTADOS BRASUL.lnk") `
    -Exe $exeAtest `
    -Icon $exeAtest `
    -Descricao "Sistema de Busca de Atestados - Brasul"

Write-Host ""
Write-Host "[3/3] SISTEMA AUDITORIA BRASUL ..."
$exeAud = Join-Path $obras "sistema_auditoria_brasul\current\SISTEMA AUDITORIA BRASUL.exe"
New-AtalhoUnc `
    -Lnk (Join-Path $obras "SISTEMA AUDITORIA BRASUL.lnk") `
    -Exe $exeAud `
    -Icon $exeAud `
    -Descricao "Sistema Auditoria - Brasul"

Write-Host ""
Write-Host "OK. Pressione F5 em 0 OBRAS."
Write-Host "Na Area de Trabalho de cada PC, rode:"
Write-Host "  powershell -ExecutionPolicy Bypass -File `"$Root\tools\corrigir_atalho_icone_maquina.ps1`" -SoDesktop"
