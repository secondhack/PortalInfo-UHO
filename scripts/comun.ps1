Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$script:ProjectPython = Join-Path $script:ProjectRoot '.venv\Scripts\python.exe'

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "El comando terminó con código $LASTEXITCODE. Revise el mensaje anterior." }
}

function Assert-ProjectPython {
    if (-not (Test-Path -LiteralPath $script:ProjectPython)) {
        throw 'Falta .venv. Desde la raíz ejecute: python -m venv .venv; después instale backend\requirements-dev.txt.'
    }
}

function Assert-ProjectNode {
    if (-not (Get-Command node.exe -ErrorAction SilentlyContinue)) { throw 'Node.js no está disponible en PATH. Instale Node 22 o posterior.' }
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'npm.cmd no está disponible en PATH.' }
    $nodeVersion = & node.exe --version
    if ($LASTEXITCODE -ne 0 -or $nodeVersion -notmatch '^v(\d+)\.' -or [int]$Matches[1] -lt 22) { throw 'Se necesita Node 22 o posterior.' }
    Write-Host "Node $nodeVersion"
    if (-not (Test-Path -LiteralPath (Join-Path $script:ProjectRoot 'frontend\node_modules\vite\package.json'))) {
        throw 'Faltan dependencias frontend. Desde la raíz ejecute: npm.cmd --prefix frontend ci --no-audit --no-fund'
    }
}

function Assert-FreePort {
    param([int]$Port)
    $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start() } catch { throw "El puerto $Port está ocupado. Use el servidor existente si es PortalInfo; no detenga procesos de otros proyectos." }
    finally { $listener.Stop() }
}
