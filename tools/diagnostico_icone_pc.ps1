# Gera relatorio de diagnostico de icones neste PC.
# Salva em %USERPROFILE%\Desktop\brasul_diagnostico_icone.txt

$ErrorActionPreference = "SilentlyContinue"
$out = Join-Path $env:USERPROFILE "Desktop\brasul_diagnostico_icone.txt"

function W { param([string]$s) Add-Content $out $s; Write-Host $s }

Remove-Item $out -Force -ErrorAction SilentlyContinue
W "=== Diagnostico icones Brasul ==="
W "Data: $(Get-Date)"
W "Usuario: $env:USERNAME"
W "PC: $env:COMPUTERNAME"
W ""

W "--- Pastas Desktop ---"
foreach ($d in @(
    [Environment]::GetFolderPath("Desktop"),
    (Join-Path $env:USERPROFILE "OneDrive\Desktop"),
    (Join-Path $env:USERPROFILE "OneDrive - Brasul Construtora\Desktop")
)) {
    W "  $d -> existe=$(Test-Path $d)"
    if (Test-Path $d) {
        Get-ChildItem $d -Filter "*PEDIDOS*.lnk" | ForEach-Object {
            $sh = New-Object -ComObject WScript.Shell
            $s = $sh.CreateShortcut($_.FullName)
            W "    $($_.Name)"
            W "      destino: $($s.TargetPath)"
            W "      icone:   $($s.IconLocation)"
        }
    }
}

W ""
W "--- Rede / 0 OBRAS ---"
foreach ($letra in "YXZWVUTSRQPONMLKJIHGFED") {
    $p = "${letra}:\0 OBRAS"
    if (Test-Path $p) {
        W "  Encontrado: $p"
        $lnk = Join-Path $p "SISTEMA DE PEDIDOS DE COMPRAS BRASUL.lnk"
        if (Test-Path $lnk) {
            $sh = New-Object -ComObject WScript.Shell
            $s = $sh.CreateShortcut($lnk)
            W "    Atalho rede destino: $($s.TargetPath)"
            W "    Atalho rede icone:   $($s.IconLocation)"
        }
        $ico = Join-Path $p "IconePedidosBrasul.ico"
        W "    IconePedidosBrasul.ico existe=$(Test-Path $ico)"
        break
    }
}

W ""
W "--- Icone local ---"
$local = Join-Path $env:LOCALAPPDATA "BrasulPedidos\SistemaPedidosV2.ico"
W "  $local -> existe=$(Test-Path $local)"
if (Test-Path $local) { W "  tamanho: $((Get-Item $local).Length) bytes" }

W ""
W "Arquivo salvo: $out"
try {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show("Diagnostico salvo em:`n$out", "Brasul") | Out-Null
} catch { }
