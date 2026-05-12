# Encerra nesta maquina processos do app que travam pastas dist/ e current/ (robocopy).
# Nao afeta outros computadores na rede — quem tiver o .exe aberto em outro PC precisa fechar la.
#
# Uso (dot-source ou direto):
#   . .\tools\close_local_sistema_pedidos.ps1
#   Invoke-CloseLocalSistemaPedidos -ProjectRoot "Z:\...\sistema_de_pedidos_brasulv2"
#
# Opcional: -IncludePythonMain encerra python.exe que esteja rodando main.py / main_patrao.py
# a partir desta pasta do projeto (cuidado se tiver mais de um terminal aberto).

function Invoke-CloseLocalSistemaPedidos {
    param(
        [string]$ProjectRoot = "",
        [switch]$IncludePythonMain,
        [switch]$Quiet
    )

    $killed = 0

    foreach ($procName in @("SistemaPedidosV2")) {
        $list = @(Get-Process -Name $procName -ErrorAction SilentlyContinue)
        foreach ($p in $list) {
            if (-not $Quiet) {
                Write-Host "  Encerrando PID $($p.Id): $procName"
            }
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            $killed++
        }
    }

    if ($IncludePythonMain -and $ProjectRoot) {
        $rootNorm = [System.IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\', '/')
        $rl = $rootNorm.ToLowerInvariant()
        try {
            $procs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue
            if ($procs) {
                foreach ($wp in @($procs)) {
                    $cmd = if ($wp.CommandLine) { $wp.CommandLine.ToLowerInvariant() } else { "" }
                    if (-not $cmd) { continue }
                    if (-not $cmd.Contains($rl)) { continue }
                    if ($cmd -notmatch 'main\.py|main_patrao\.py') { continue }
                    if (-not $Quiet) {
                        Write-Host "  Encerrando PID $($wp.ProcessId): python (main do projeto)"
                    }
                    Stop-Process -Id $wp.ProcessId -Force -ErrorAction SilentlyContinue
                    $killed++
                }
            }
        }
        catch {
            if (-not $Quiet) {
                Write-Host "  (Aviso) Nao foi possivel listar python.exe via WMI: $_"
            }
        }
    }

    if ($killed -gt 0) {
        Start-Sleep -Milliseconds 1200
    }
    return $killed
}
