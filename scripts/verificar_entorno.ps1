param([switch]$SinBaseDeDatos)
. (Join-Path $PSScriptRoot 'comun.ps1')
try {
    Push-Location $script:ProjectRoot
    Assert-ProjectPython
    Assert-ProjectNode
    $checkArgs = @('scripts\check_environment.py')
    if ($SinBaseDeDatos) { $checkArgs += '--skip-database' }
    Invoke-Checked $script:ProjectPython $checkArgs
    Write-Host 'Entorno comprobado. No se modificó PostgreSQL ni la configuración global.' -ForegroundColor Green
} catch { Write-Error $_; exit 1 }
finally { Pop-Location }
