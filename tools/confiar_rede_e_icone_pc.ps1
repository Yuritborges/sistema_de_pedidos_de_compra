# Configura ESTE PC para confiar no servidor Brasul e exibir icones de atalhos na rede.
# Rode no PC da Thamyres (nao coloca arquivos em 0 OBRAS).
#
#   powershell -ExecutionPolicy Bypass -File "\\192.168.15.250\arquivos brasul\0 OBRAS\sistema_de_pedidos_brasulv2\tools\confiar_rede_e_icone_pc.ps1"
#
# Parte HKCU (zona intranet): nao precisa ser administrador.
# Parte HKLM (icone remoto): pede elevacao se possivel.

$ErrorActionPreference = "Stop"
$Servidor = "192.168.15.250"
$Unc = "\\$Servidor\arquivos brasul"

function Log { param([string]$Msg) Write-Host $Msg }

Log "=== Confiar rede Brasul (usuario: $env:USERNAME) ==="
Log ""

# 1) Servidor na zona Intranet local (remove aviso "fora da rede local")
Log "[1/3] Marcando $Servidor como Intranet local (HKCU) ..."
$zoneBase = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMapKey"

New-Item -Path "$zoneBase\UNC\$Servidor" -Force | Out-Null
New-ItemProperty -Path "$zoneBase\UNC\$Servidor" -Name "file" -Value 1 -PropertyType DWord -Force | Out-Null

New-Item -Path "$zoneBase\Domains\$Servidor" -Force | Out-Null
New-ItemProperty -Path "$zoneBase\Domains\$Servidor" -Name "file" -Value 1 -PropertyType DWord -Force | Out-Null

# Range 192.168.15.0/24 (alguns Windows so aplicam por faixa IP)
$rangePath = "$zoneBase\Range"
New-Item -Path $rangePath -Force | Out-Null
$rangeName = "BrasulLAN"
New-Item -Path "$rangePath\$rangeName" -Force | Out-Null
New-ItemProperty -Path "$rangePath\$rangeName" -Name ":Range" -Value "192.168.15.*" -PropertyType String -Force | Out-Null
New-ItemProperty -Path "$rangePath\$rangeName" -Name "file" -Value 1 -PropertyType DWord -Force | Out-Null

Log "  OK: $Servidor e faixa 192.168.15.* como Intranet"
Log ""

# 2) Permitir icones de atalho apontando para caminho de rede (HKLM - precisa admin)
Log "[2/3] Permitindo icones em caminhos remotos (HKLM) ..."
$explorerPol = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Explorer"
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if ($isAdmin) {
    New-Item -Path $explorerPol -Force | Out-Null
    New-ItemProperty -Path $explorerPol -Name "EnableShellShortcutIconRemotePath" -Value 1 -PropertyType DWord -Force | Out-Null
    Log "  OK: EnableShellShortcutIconRemotePath = 1"
} else {
    Log "  AVISO: rode como Administrador para aplicar icone remoto no registro."
    Log "  (A Intranet acima ja foi aplicada para este usuario.)"
}

Log ""

# 3) Atalho na Area de Trabalho com icone local
Log "[3/3] Instalando atalho na Area de Trabalho (icone local) ..."
$instalar = Join-Path $PSScriptRoot "instalar_pedidos_area_trabalho.ps1"
if (Test-Path $instalar) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $instalar
} else {
    Log "  Script instalar_pedidos_area_trabalho.ps1 nao encontrado."
}

Log ""
Log "Pronto. Reinicie o PC ou reinicie o Explorador de Arquivos."
Log "Depois: F5 em Y:\0 OBRAS e teste o atalho Pedidos Brasul na Area de Trabalho."
