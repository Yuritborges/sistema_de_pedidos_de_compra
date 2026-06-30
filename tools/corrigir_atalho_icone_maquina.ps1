# Corrige atalho NESTE PC (principalmente Area de Trabalho).
# O icone fica em disco LOCAL — Windows nao exibe .ico so na rede no Explorer.
#
# Thamyres / qualquer PC:
#   powershell -ExecutionPolicy Bypass -File "\\192.168.15.250\arquivos brasul\0 OBRAS\sistema_de_pedidos_brasulv2\tools\corrigir_atalho_icone_maquina.ps1"
#
# So area de trabalho (recomendado em cada PC):
#   ... -SoDesktop
#
# So atalho na pasta da rede (use uma vez no servidor):
#   ... -SoRede

param(
    [switch]$SoDesktop,
    [switch]$SoRede,
    [string]$NomeAtalho = "SISTEMA DE PEDIDOS DE COMPRAS BRASUL"
)

$ErrorActionPreference = "Stop"

if (-not $SoDesktop -and -not $SoRede) {
    $SoDesktop = $true
    $SoRede = $true
}

function Find-ObrasDir {
    $candidatos = @()
    foreach ($letra in "ZYXWVUTSRQPONMLKJIHGFED") {
        $candidatos += "${letra}:\0 OBRAS"
    }
    $candidatos += "\\192.168.15.250\arquivos brasul\0 OBRAS"
    foreach ($p in $candidatos) {
        if (Test-Path $p) { return $p }
    }
    throw "Nao encontrei a pasta 0 OBRAS (Z:, Y: ou UNC)."
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
            return $uncRoot + $resolved.Substring(2)
        }
    }
    return $resolved
}

function Resolve-IconeOrigem {
    param([string]$ObrasDir, [string]$ProjDir)
    $candidatos = @(
        (Join-Path $ProjDir "current\SistemaPedidosV2.ico"),
        (Join-Path $ProjDir "assets\logos\logo_brasul.ico"),
        (Join-Path $ProjDir "assets\iconebrasul2.ico")
    )
    foreach ($p in $candidatos) {
        if (Test-Path $p) { return $p }
    }
    throw "Icone nao encontrado em current\ ou assets\."
}

function Fix-Atalho {
    param(
        [string]$CaminhoLnk,
        [string]$ExePath,
        [string]$IconPath,
        [switch]$IconeLocal
    )
    if (-not (Test-Path $ExePath)) {
        Write-Host "  [ERRO] Exe nao encontrado: $ExePath"
        return $false
    }
    if (-not (Test-Path $IconPath)) {
        Write-Host "  [ERRO] Icone nao encontrado: $IconPath"
        return $false
    }
    $dir = Split-Path $CaminhoLnk -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $Wsh = New-Object -ComObject WScript.Shell
    $sc = $Wsh.CreateShortcut($CaminhoLnk)
    $sc.TargetPath = Convert-PathToUnc $ExePath
    $sc.WorkingDirectory = Convert-PathToUnc (Split-Path $ExePath -Parent)
    if ($IconeLocal) {
        $sc.IconLocation = "$IconPath,0"
    } else {
        $sc.IconLocation = "$(Convert-PathToUnc $IconPath),0"
    }
    $sc.Description = "Sistema de Pedidos - Brasul Construtora"
    $sc.Save()
    Write-Host "  OK: $CaminhoLnk"
    Write-Host "       destino -> $($sc.TargetPath)"
    Write-Host "       icone   -> $($sc.IconLocation)"
    return $true
}

$obras = Find-ObrasDir
$proj = Join-Path $obras "sistema_de_pedidos_brasulv2"
$exe = Join-Path $proj "current\SistemaPedidosV2.exe"
$iconOrigem = Resolve-IconeOrigem -ObrasDir $obras -ProjDir $proj

$localDir = Join-Path $env:LOCALAPPDATA "BrasulPedidos"
New-Item -ItemType Directory -Path $localDir -Force | Out-Null
$iconLocal = Join-Path $localDir "SistemaPedidosV2.ico"
Copy-Item $iconOrigem $iconLocal -Force
Write-Host "Icone local (este PC): $iconLocal"
Write-Host ""

if ($SoDesktop) {
    Write-Host "Area de Trabalho ..."
    $desktop = [Environment]::GetFolderPath("Desktop")
    Fix-Atalho `
        -CaminhoLnk (Join-Path $desktop "$NomeAtalho.lnk") `
        -ExePath $exe `
        -IconPath $iconLocal `
        -IconeLocal | Out-Null
}

if ($SoRede) {
    Write-Host "Pasta da rede ($obras) ..."
    Fix-Atalho `
        -CaminhoLnk (Join-Path $obras "$NomeAtalho.lnk") `
        -ExePath $exe `
        -IconPath $exe | Out-Null
}

Write-Host ""
Write-Host "Pronto."
Write-Host "- F5 no Explorer (pasta 0 OBRAS e Area de Trabalho)."
Write-Host "- Se ainda branco: reinicie o PC ou apague o atalho antigo da area de trabalho e rode de novo."
