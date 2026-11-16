param([switch]$SoloVerificar)
. (Join-Path $PSScriptRoot 'comun.ps1')
try {
    Push-Location $script:ProjectRoot
    Assert-ProjectPython
    Invoke-Checked $script:ProjectPython @('scripts\check_environment.py')
    if (-not $SoloVerificar) {
        Assert-FreePort 8010
        Write-Host 'Backend: http://127.0.0.1:8010/api/health/ | Swagger: http://127.0.0.1:8010/api/docs/'
        Invoke-Checked $script:ProjectPython @('-u','scripts\serve_backend.py')
    }
} catch { Write-Error $_; exit 1 }
finally { Pop-Location }
