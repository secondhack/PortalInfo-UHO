param([switch]$SoloVerificar)
. (Join-Path $PSScriptRoot 'comun.ps1')
try {
    Push-Location $script:ProjectRoot
    Assert-ProjectPython
    Assert-ProjectNode
    Invoke-Checked $script:ProjectPython @('scripts\check_environment.py')
    if (-not $SoloVerificar) {
        Assert-FreePort 5174
        Write-Host 'Panel administrativo: http://127.0.0.1:5174'
        Invoke-Checked 'npm.cmd' @('--prefix','frontend','run','dev')
    }
} catch { Write-Error $_; exit 1 }
finally { Pop-Location }
