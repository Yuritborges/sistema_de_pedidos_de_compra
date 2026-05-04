# Funcao interna: espelha Source -> Dest com robocopy (caminhos com espacos OK).
# Retorna o codigo de saida do robocopy (0-7 = OK com arquivos copiados ou nada a fazer; 8+ = problema).

function Invoke-RobocopyMirror {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [int]$Retries = 30,
        [int]$WaitSeconds = 3
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "robocopy.exe"
    $psi.Arguments = "`"$Source`" `"$Destination`" /MIR /R:$Retries /W:$WaitSeconds /NFL /NDL /NJH /NJS /NP"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    return $p.ExitCode
}
