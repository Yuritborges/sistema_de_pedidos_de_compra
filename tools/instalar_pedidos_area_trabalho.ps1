# Instala atalho do Pedidos na Area de Trabalho DESTE PC (icone local).
# Use no PC da Thamyres: duplo clique em INSTALAR_ATALHO_PEDIDOS.bat em 0 OBRAS.
#
#   powershell -ExecutionPolicy Bypass -File "...\tools\instalar_pedidos_area_trabalho.ps1"

$ErrorActionPreference = "Stop"

$LogFile = Join-Path $env:TEMP "brasul_pedidos_instalacao.log"
$NomeAtalho = "SISTEMA DE PEDIDOS DE COMPRAS BRASUL"
$NomeAtalhoCurto = "Pedidos Brasul"

function Log {
    param([string]$Msg)
    $line = "$(Get-Date -Format 'HH:mm:ss') $Msg"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $Msg
}

function Show-Msg {
    param([string]$Text, [string]$Title = "Pedidos Brasul")
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        [System.Windows.Forms.MessageBox]::Show($Text, $Title) | Out-Null
    } catch {
        Write-Host $Text
    }
}

function Get-DesktopPaths {
    $paths = New-Object System.Collections.Generic.List[string]

    $known = [Environment]::GetFolderPath("Desktop")
    if ($known -and (Test-Path $known)) { $paths.Add($known) | Out-Null }

    $oneDrive = Join-Path $env:USERPROFILE "OneDrive\Desktop"
    if (Test-Path $oneDrive) { $paths.Add($oneDrive) | Out-Null }

    $oneDriveBiz = Join-Path $env:USERPROFILE "OneDrive - Brasul Construtora\Desktop"
    if (Test-Path $oneDriveBiz) { $paths.Add($oneDriveBiz) | Out-Null }

    try {
        $reg = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" -ErrorAction SilentlyContinue
        if ($reg.Desktop) {
            $expanded = [Environment]::ExpandEnvironmentVariables($reg.Desktop)
            if ($expanded -and (Test-Path $expanded)) { $paths.Add($expanded) | Out-Null }
        }
    } catch { }

    $public = [Environment]::GetFolderPath("CommonDesktopDirectory")
    if ($public -and (Test-Path $public)) { $paths.Add($public) | Out-Null }

    return ($paths | Select-Object -Unique)
}

function Find-ObrasDir {
    foreach ($letra in "YXZWVUTSRQPONMLKJIHGFED") {
        $p = "${letra}:\0 OBRAS"
        if (Test-Path $p) { return $p }
    }
    $unc = "\\192.168.15.250\arquivos brasul\0 OBRAS"
    if (Test-Path $unc) { return $unc }
    throw "Nao encontrei 0 OBRAS (Y:, Z: ou rede)."
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

function Remove-AtalhosAntigos {
    param([string[]]$Pastas)
    $padroes = @(
        "*PEDIDOS*BRASUL*",
        "*COMPRAS*BRASUL*",
        "SISTEMA DE PEDIDOS*"
    )
    foreach ($pasta in $Pastas) {
        foreach ($padrao in $padroes) {
            Get-ChildItem -Path $pasta -Filter "$padrao.lnk" -ErrorAction SilentlyContinue | ForEach-Object {
                Log "  Removendo atalho antigo: $($_.FullName)"
                Remove-Item $_.FullName -Force
            }
        }
    }
}

function New-AtalhoLocal {
    param(
        [string]$CaminhoLnk,
        [string]$ExePath,
        [string]$IconLocal
    )
    $dir = Split-Path $CaminhoLnk -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $Wsh = New-Object -ComObject WScript.Shell
    $sc = $Wsh.CreateShortcut($CaminhoLnk)
    $sc.TargetPath = Convert-PathToUnc $ExePath
    $sc.WorkingDirectory = Convert-PathToUnc (Split-Path $ExePath -Parent)
    $sc.IconLocation = "$IconLocal,0"
    $sc.Description = "Sistema de Pedidos - Brasul Construtora"
    $sc.Save()
    return $sc
}

# --- inicio ---
"" | Set-Content -Path $LogFile -Encoding UTF8
Log "Usuario: $env:USERNAME | PC: $env:COMPUTERNAME"
Log "Log: $LogFile"
Log ""

try {
    $obras = Find-ObrasDir
    $proj = Join-Path $obras "sistema_de_pedidos_brasulv2"
    $exe = Join-Path $proj "current\SistemaPedidosV2.exe"

    if (-not (Test-Path $exe)) {
        throw "Programa nao encontrado: $exe"
    }
    Log "Exe OK: $exe"

    $iconOrigem = $null
    foreach ($c in @(
        (Join-Path $obras "IconePedidosBrasul.ico"),
        (Join-Path $proj "current\SistemaPedidosV2.ico"),
        (Join-Path $proj "assets\logos\logo_brasul.ico"),
        (Join-Path $proj "assets\iconebrasul2.ico")
    )) {
        if (Test-Path $c) { $iconOrigem = $c; break }
    }
    if (-not $iconOrigem) {
        throw "Arquivo .ico nao encontrado na rede."
    }
    Log "Icone origem: $iconOrigem"

    $localDir = Join-Path $env:LOCALAPPDATA "BrasulPedidos"
    New-Item -ItemType Directory -Path $localDir -Force | Out-Null
    $iconLocal = Join-Path $localDir "SistemaPedidosV2.ico"
    Copy-Item $iconOrigem $iconLocal -Force
    $tam = (Get-Item $iconLocal).Length
    if ($tam -lt 1000) {
        throw "Copia do icone falhou (arquivo muito pequeno: $tam bytes)."
    }
    Log "Icone local: $iconLocal ($tam bytes)"

    $desktops = Get-DesktopPaths
    if ($desktops.Count -eq 0) {
        throw "Nenhuma pasta de Area de Trabalho encontrada."
    }
    Log "Pastas Desktop encontradas:"
    foreach ($d in $desktops) { Log "  - $d" }

    Log ""
    Log "Removendo atalhos antigos ..."
    Remove-AtalhosAntigos -Pastas $desktops

    Log ""
    Log "Criando atalhos novos ..."
    $criados = @()
    foreach ($desktop in $desktops) {
        foreach ($nome in @($NomeAtalho, $NomeAtalhoCurto)) {
            $lnk = Join-Path $desktop "$nome.lnk"
            $sc = New-AtalhoLocal -CaminhoLnk $lnk -ExePath $exe -IconLocal $iconLocal
            Log "  OK: $lnk"
            Log "       destino -> $($sc.TargetPath)"
            Log "       icone   -> $($sc.IconLocation)"
            $criados += $lnk
        }
        $icoDesktop = Join-Path $desktop "IconePedidosBrasul.ico"
        Copy-Item $iconLocal $icoDesktop -Force -ErrorAction SilentlyContinue
    }

    Log ""
    Log "Limpando cache de icones ..."
    $ErrorActionPreference = "SilentlyContinue"
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    $cacheBase = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Explorer"
    Get-ChildItem $cacheBase -Filter "iconcache*" -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Start-Process "ie4uinit.exe" -ArgumentList "-show" -Wait -ErrorAction SilentlyContinue
    Start-Process explorer
    $ErrorActionPreference = "Stop"

    $msg = @"
Instalacao concluida!

Procure na Area de Trabalho o atalho:
  $NomeAtalhoCurto
  (ou $NomeAtalho)

O icone fica neste PC (nao depende da pasta de rede).

IMPORTANTE: Na pasta Y:\0 OBRAS os icones podem continuar brancos - isso e limitacao do Windows em alguns PCs. Use o atalho da Area de Trabalho.

Log salvo em:
$LogFile
"@
    Log ""
    Log "Concluido."
    Show-Msg $msg

    $primeiroDesktop = $desktops[0]
    Start-Process explorer.exe -ArgumentList "`"$primeiroDesktop`""
}
catch {
    Log "ERRO: $($_.Exception.Message)"
    Show-Msg "Erro na instalacao:`n`n$($_.Exception.Message)`n`nVeja o log:`n$LogFile" "Pedidos Brasul - Erro"
    exit 1
}
