# Cria tag de versao (vX.Y.Z), envia ao GitHub e dispara build + Release automaticos.
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 2.1.1
#   powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 2.1.1 -Mensagem "Correcao PDF obra"

param(
    [Parameter(Mandatory = $true)]
    [string]$Versao,
    [string]$Mensagem = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if ($Versao -match '^v') { $Versao = $Versao.Substring(1) }
if ($Versao -notmatch '^\d+\.\d+\.\d+$') {
    throw "Versao invalida: use formato X.Y.Z (ex.: 2.1.1)"
}

$tag = "v$Versao"
if ($Mensagem) {
    $msg = $Mensagem
} else {
    $msg = "Release $tag - Sistema de Pedidos Brasul"
}

$dirty = git status --porcelain
if ($dirty) {
    Write-Warning "Ha alteracoes nao commitadas. Commit e push antes da tag, ou a Release nao tera esse codigo."
    $r = Read-Host "Continuar mesmo assim? (s/N)"
    if ($r -notin @('s', 'S', 'sim', 'Sim')) { exit 1 }
}

$exists = git tag -l $tag
if ($exists) {
    throw "Tag $tag ja existe. Escolha outro numero (ex.: bump patch)."
}

Write-Host "Criando tag $tag ..."
git tag -a $tag -m $msg
Write-Host "Enviando tag para origin (dispara GitHub Actions + Release) ..."
git push origin $tag

Write-Host ""
Write-Host "OK Tag $tag enviada."
Write-Host "  1) GitHub -> Actions -> aguarde build verde"
Write-Host "  2) GitHub -> Releases -> baixe $tag"
Write-Host "  3) tools\publicar_build_na_rede.ps1 -Origem <pasta extraida>"
