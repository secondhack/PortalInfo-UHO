param([switch]$SoloVerificar)
. (Join-Path $PSScriptRoot 'comun.ps1')
try {
    Push-Location $script:ProjectRoot
    Assert-ProjectPython
    Assert-ProjectNode
    Invoke-Checked $script:ProjectPython @('scripts\check_environment.py')
    Invoke-Checked 'node.exe' @('captive-portal/build.mjs')
    Invoke-Checked $script:ProjectPython @('scripts\check_portal_size.py')
    if (-not $SoloVerificar) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8010/api/health/' -TimeoutSec 8
            if ($health.status -ne 'ok') { throw 'Backend no disponible.' }
            $portal = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8010/portal/' -TimeoutSec 8
            if ($portal.StatusCode -ne 200) { throw 'Portal no disponible.' }
        } catch { throw 'Inicie primero scripts\iniciar_backend.ps1 en la terminal 1. No es necesario un tercer servidor.' }
    }
    Write-Host 'Portal: http://127.0.0.1:8010/portal/ · servido por Django; esta terminal queda libre.' -ForegroundColor Green
    Write-Host 'Visitantes ficticios: .local\portal-demo-credentials.txt. No modifican Internet.'
} catch { Write-Error $_; exit 1 }
finally { Pop-Location }
