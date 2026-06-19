# Copia .ico ao lado do .exe (Explorer/atalho na rede) e opcionalmente recria atalho na Area de Trabalho.
#
# Windows costuma NAO mostrar icone embutido no .exe em pasta de rede (Z:/Y:).
# O icone na barra de tarefas vem do programa aberto; atalho precisa apontar para o .ico explicito.
#
# Uso (na raiz do projeto):
#   powershell -ExecutionPolicy Bypass -File tools\publicar_icone_atalho.ps1
#   powershell -ExecutionPolicy Bypass -File tools\publicar_icone_atalho.ps1 -CriarAtalhoDesktop
#   powershell -ExecutionPolicy Bypass -File tools\publicar_icone_atalho.ps1 -PastaAtalho "Y:\0 OBRAS\Atalhos"

param(
    [switch]$CriarAtalhoDesktop,
    [string]$PastaAtalho = "",
    [string]$NomeAtalho = "Sistema de Pedidos Brasul"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

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

function Publish-IconeEm {
    param([string]$PastaDestino)
    if (-not (Test-Path $PastaDestino)) { return $false }
    $origem = Get-IconeOrigem
    $destino = Join-Path $PastaDestino "SistemaPedidosV2.ico"
    Copy-Item -Path $origem -Destination $destino -Force
    Write-Host "  Icone: $destino"
    return $true
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
    $Wsh = New-Object -ComObject WScript.Shell
    $sc = $Wsh.CreateShortcut($CaminhoLnk)
    $sc.TargetPath = $ExePath
    $sc.WorkingDirectory = Split-Path $ExePath -Parent
    if (Test-Path $IconPath) {
        $sc.IconLocation = "$IconPath,0"
    }
    $sc.Description = "Sistema de Pedidos - Brasul Construtora"
    $sc.Save()
    Write-Host "  Atalho: $CaminhoLnk"
}

$cur = Join-Path $Root "current"
$exe = Join-Path $cur "SistemaPedidosV2.exe"
if (-not (Test-Path $exe)) {
    throw "Nao encontrei $exe. Rode build_release.ps1 antes."
}

Write-Host "Publicando icone em current\ ..."
Publish-IconeEm -PastaDestino $cur | Out-Null
$icon = Join-Path $cur "SistemaPedidosV2.ico"

# Tambem em releases mais recente (opcional)
$releases = Join-Path $Root "releases"
if (Test-Path $releases) {
    $ultimo = Get-ChildItem $releases -Directory -Filter "SistemaPedidosV2_*" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($ultimo) {
        Publish-IconeEm -PastaDestino $ultimo.FullName | Out-Null
    }
}

if ($CriarAtalhoDesktop) {
    Write-Host "Criando atalho na Area de Trabalho ..."
    $desktop = [Environment]::GetFolderPath("Desktop")
    New-AtalhoPedidos -CaminhoLnk (Join-Path $desktop "$NomeAtalho.lnk") -ExePath $exe -IconPath $icon
}

if ($PastaAtalho) {
    Write-Host "Criando atalho em $PastaAtalho ..."
    New-AtalhoPedidos -CaminhoLnk (Join-Path $PastaAtalho "$NomeAtalho.lnk") -ExePath $exe -IconPath $icon
}

Write-Host ""
Write-Host "OK. Se um atalho antigo ainda mostra icone branco:"
Write-Host "  Botao direito no atalho -> Propriedades -> Alterar icone -> escolha:"
Write-Host "  $icon"
