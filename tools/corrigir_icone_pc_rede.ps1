# Correcao completa para PC que NAO mostra icones na pasta de rede.
# Rodar NO PC da Thamyres (PowerShell como usuario normal):
#
#   powershell -ExecutionPolicy Bypass -File "\\192.168.15.250\arquivos brasul\0 OBRAS\sistema_de_pedidos_brasulv2\tools\corrigir_icone_pc_rede.ps1"

$ErrorActionPreference = "Stop"
$Root = "\\192.168.15.250\arquivos brasul\0 OBRAS\sistema_de_pedidos_brasulv2"
$Tools = Join-Path $Root "tools"

Write-Host "=== Correcao de icones (este PC) ==="
Write-Host ""

Write-Host "[1/4] Testando acesso a rede ..."
$exe = Join-Path $Root "current\SistemaPedidosV2.exe"
$ico = "\\192.168.15.250\arquivos brasul\0 OBRAS\IconePedidosBrasul.ico"
foreach ($p in @($exe, $ico)) {
    if (Test-Path $p) { Write-Host "  OK: $p" }
    else { Write-Host "  FALHOU: $p"; throw "Sem acesso. Verifique VPN/rede." }
}

Write-Host ""
Write-Host "[2/4] Limpando cache de icones do Windows ..."
& powershell -ExecutionPolicy Bypass -File (Join-Path $Tools "limpar_cache_icone_windows.ps1")

Write-Host ""
Write-Host "[3/4] Atalho Area de Trabalho (icone local) ..."
& powershell -ExecutionPolicy Bypass -File (Join-Path $Tools "corrigir_atalho_icone_maquina.ps1") -SoDesktop

Write-Host ""
Write-Host "[4/4] Conferindo atalhos na pasta 0 OBRAS ..."
$sh = New-Object -ComObject WScript.Shell
$obras = $null
foreach ($letra in "YXZWVUTSRQPONMLKJIHGFED") {
    $p = "${letra}:\0 OBRAS"
    if (Test-Path $p) { $obras = $p; break }
}
if ($obras) {
    $lnk = Join-Path $obras "SISTEMA DE PEDIDOS DE COMPRAS BRASUL.lnk"
    if (Test-Path $lnk) {
        $s = $sh.CreateShortcut($lnk)
        Write-Host "  Atalho rede: $lnk"
        Write-Host "  Destino: $($s.TargetPath)"
        Write-Host "  Icone: $($s.IconLocation)"
    }
}

Write-Host ""
Write-Host "Pronto. Abra Y:\0 OBRAS (ou Z:) e pressione F5."
Write-Host "Se ainda branco na pasta de rede, use o atalho da Area de Trabalho."
Write-Host "La o icone fica fixo neste PC."
