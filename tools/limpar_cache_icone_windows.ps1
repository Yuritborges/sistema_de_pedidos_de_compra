# Limpa cache de icones do Windows e reinicia o Explorer.
# Rode no PC que nao mostra icones na pasta de rede (ex.: Thamyres).
#
#   powershell -ExecutionPolicy Bypass -File "\\192.168.15.250\arquivos brasul\0 OBRAS\sistema_de_pedidos_brasulv2\tools\limpar_cache_icone_windows.ps1"

$ErrorActionPreference = "SilentlyContinue"

Write-Host "Encerrando Explorer ..."
Stop-Process -Name explorer -Force
Start-Sleep -Seconds 2

$base = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Explorer"
Get-ChildItem $base -Filter "iconcache*" -Force | Remove-Item -Force
Get-ChildItem $base -Filter "thumbcache*" -Force | Remove-Item -Force

Write-Host "Reconstruindo cache de icones ..."
Start-Process "ie4uinit.exe" -ArgumentList "-show" -Wait

Write-Host "Reiniciando Explorer ..."
Start-Process explorer

Write-Host ""
Write-Host "OK. Abra 0 OBRAS de novo (Y: ou Z:) e pressione F5."
