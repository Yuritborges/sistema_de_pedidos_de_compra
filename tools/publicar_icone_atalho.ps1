# Copia .ico ao lado do .exe e recria atalhos com caminhos UNC (funciona com Z:, Y:, etc.).
#
# Atalho na pasta de rede: icone embutido no .exe (sem .ico extra em 0 OBRAS).
# Area de trabalho: icone copiado para %LOCALAPPDATA%\BrasulPedidos (Windows nao acha .ico so na rede).
#
# Uso (na raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File tools\publicar_icone_atalho.ps1
#   powershell -ExecutionPolicy Bypass -File tools\publicar_icone_atalho.ps1 -CriarAtalhoDesktop
#   powershell -ExecutionPolicy Bypass -File tools\publicar_icone_atalho.ps1 -PastaAtalho "Z:\0 OBRAS" -NomeAtalho "SISTEMA DE PEDIDOS DE COMPRAS BRASUL"

param(
    [switch]$CriarAtalhoDesktop,
    [string]$PastaAtalho = "",
    [string]$NomeAtalho = "Sistema de Pedidos Brasul"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$IconeNomeRede = "IconePedidosBrasul.ico"
$IconeNomeLocal = "SistemaPedidosV2.ico"

function Get-IconeOrigem {
    $candidatos = @(
        (Join-Path $Root "assets\iconebrasul2.ico"),
        (Join-Path $Root "assets\logos\logo_brasul.ico"),
        (Join-Path $Root "assets\logo.ico")
    )
    foreach ($p in $candidatos) {
        if (Test-Path $p) { return $p }
    }
    throw "Nenhum .ico encontrado em assets\ (logo_brasul.ico ou iconebrasul2.ico)."
}

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
            $rel = $resolved.Substring(2)  # remove "Z:"
            return $uncRoot + $rel
        }
    }
    return $resolved
}

function Publish-IconeEm {
    param(
        [string]$PastaDestino,
        [string]$NomeArquivo = $IconeNomeLocal
    )
    if (-not (Test-Path $PastaDestino)) { return $null }
    $origem = Get-IconeOrigem
    $destino = Join-Path $PastaDestino $NomeArquivo
    Copy-Item -Path $origem -Destination $destino -Force
    Write-Host "  Icone: $destino"
    return $destino
}

function New-AtalhoPedidos {
    param(
        [string]$CaminhoLnk,
        [string]$ExePath,
        [string]$IconPath
    )
    $dir = Split-Path $CaminhoLnk -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    $exeUnc = Convert-PathToUnc $ExePath
    $iconUnc = Convert-PathToUnc $IconPath
    $workUnc = Convert-PathToUnc (Split-Path $ExePath -Parent)

    $Wsh = New-Object -ComObject WScript.Shell
    $sc = $Wsh.CreateShortcut($CaminhoLnk)
    $sc.TargetPath = $exeUnc
    $sc.WorkingDirectory = $workUnc
    if (Test-Path $IconPath) {
        $sc.IconLocation = "$iconUnc,0"
    } elseif (Test-Path $ExePath) {
        $sc.IconLocation = "$exeUnc,0"
    }
    $sc.Description = "Sistema de Pedidos - Brasul Construtora"
    $sc.Save()
    Write-Host "  Atalho: $CaminhoLnk"
    Write-Host "  Destino (UNC): $($sc.TargetPath)"
    Write-Host "  Icone (UNC):   $($sc.IconLocation)"
}

$cur = Join-Path $Root "current"
$exe = Join-Path $cur "SistemaPedidosV2.exe"
if (-not (Test-Path $exe)) {
    throw "Nao encontrei $exe. Rode build_release.ps1 antes."
}

Write-Host "Publicando icone em current\ ..."
Publish-IconeEm -PastaDestino $cur | Out-Null
$iconCurrent = Join-Path $cur $IconeNomeLocal

$releases = Join-Path $Root "releases"
if (Test-Path $releases) {
    $ultimo = Get-ChildItem $releases -Directory -Filter "SistemaPedidosV2_*" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($ultimo) {
        Publish-IconeEm -PastaDestino $ultimo.FullName | Out-Null
    }
}

if ($PastaAtalho) {
    Write-Host "Atualizando atalho em $PastaAtalho (icone do .exe, sem arquivos novos) ..."
    New-AtalhoPedidos `
        -CaminhoLnk (Join-Path $PastaAtalho "$NomeAtalho.lnk") `
        -ExePath $exe `
        -IconPath $exe
}

if ($CriarAtalhoDesktop) {
    Write-Host "Criando atalho na Area de Trabalho (icone local) ..."
    $localDir = Join-Path $env:LOCALAPPDATA "BrasulPedidos"
    New-Item -ItemType Directory -Path $localDir -Force | Out-Null
    $iconLocal = Publish-IconeEm -PastaDestino $localDir -NomeArquivo $IconeNomeLocal
    $desktop = [Environment]::GetFolderPath("Desktop")
    New-AtalhoPedidos `
        -CaminhoLnk (Join-Path $desktop "$NomeAtalho.lnk") `
        -ExePath $exe `
        -IconPath $iconLocal
}

Write-Host ""
Write-Host "OK. Atalhos usam caminho UNC (vale para Z:, Y: ou sem letra de unidade)."
Write-Host "Na maquina da Thamyres: F5 na pasta ou rode tools\corrigir_atalho_icone_maquina.ps1"
