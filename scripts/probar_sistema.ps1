param([switch]$ConHTTP,[switch]$ConNavegador)
. (Join-Path $PSScriptRoot 'comun.ps1')
try {
    Push-Location $script:ProjectRoot
    Assert-ProjectPython
    Assert-ProjectNode
    Invoke-Checked $script:ProjectPython @('scripts\check_environment.py')
    Invoke-Checked $script:ProjectPython @('backend\manage.py','check')
    Invoke-Checked $script:ProjectPython @('backend\manage.py','makemigrations','--check','--dry-run')
    Invoke-Checked $script:ProjectPython @('backend\manage.py','migrate','--check')
    Invoke-Checked $script:ProjectPython @('-m','pip','check')
    Invoke-Checked $script:ProjectPython @('scripts\verificar_secretos.py')
    Invoke-Checked 'node.exe' @('captive-portal/build.mjs')
    Invoke-Checked $script:ProjectPython @('scripts\check_portal_size.py')
    Invoke-Checked $script:ProjectPython @('backend\manage.py','test','apps.accounts','apps.content','apps.analytics','apps.portal','--keepdb','--noinput','--verbosity','1')
    Invoke-Checked 'node.exe' @('--test','captive-portal/tests/portal.test.cjs')
    Invoke-Checked 'npm.cmd' @('--prefix','frontend','test')
    Invoke-Checked 'npm.cmd' @('--prefix','frontend','run','build')
    Invoke-Checked $script:ProjectPython @('backend\manage.py','spectacular','--validate','--file','docs\arquitectura\openapi.yaml')
    if ($ConHTTP) { Invoke-Checked $script:ProjectPython @('scripts\smoke_final_http.py') }
    if ($ConNavegador) { Invoke-Checked (Join-Path $script:ProjectRoot 'frontend\node_modules\.bin\playwright.cmd') @('test','--config','frontend/playwright.config.js') }
    Write-Host 'Comprobaciones terminadas sin fallos. Consulte el alcance en docs\pruebas\RESULTADOS.md.' -ForegroundColor Green
} catch { Write-Error $_; exit 1 }
finally { Pop-Location }
