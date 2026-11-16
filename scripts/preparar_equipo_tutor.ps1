# Prepara PostgreSQL local en un equipo Windows nuevo del tutor.
# Usa la contraseña ya guardada en .env. No la imprime.
# No toca un clúster que ya exista.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$data = Join-Path $root '.local\postgres'
if (Test-Path $data) {
    throw 'Ya existe .local\postgres. No se reinicializa ni se restaura encima.'
}
if (-not (Test-Path (Join-Path $root '.env'))) {
    throw 'Falta .env en la raíz del proyecto.'
}

function Read-EnvValue([string]$name) {
    foreach ($line in Get-Content -LiteralPath (Join-Path $root '.env') -Encoding UTF8) {
        $trim = $line.Trim()
        if ($trim.StartsWith("$name=")) {
            return $trim.Substring($name.Length + 1).Trim().Trim('"').Trim("'")
        }
    }
    throw "Falta $name en .env."
}

$dbUser = Read-EnvValue 'DATABASE_USER'
$dbPass = Read-EnvValue 'DATABASE_PASSWORD'
$dbName = Read-EnvValue 'DATABASE_NAME'
$dbPort = Read-EnvValue 'DATABASE_PORT'
if ($dbName -notmatch '^[A-Za-z][A-Za-z0-9_]{0,62}$') { throw 'DATABASE_NAME no es un identificador seguro.' }
if ($dbUser -notmatch '^[A-Za-z][A-Za-z0-9_]{0,62}$') { throw 'DATABASE_USER no es un identificador seguro.' }
if ($dbPort -notmatch '^[0-9]{2,5}$') { throw 'DATABASE_PORT no es válido.' }

$pg = 'C:\Program Files\PostgreSQL\16\bin'
$initdb = Join-Path $pg 'initdb.exe'
$pgctl = Join-Path $pg 'pg_ctl.exe'
$psql = Join-Path $pg 'psql.exe'
$restore = Join-Path $pg 'pg_restore.exe'
foreach ($tool in @($initdb, $pgctl, $psql, $restore)) {
    if (-not (Test-Path $tool)) { throw "No se encontró $tool. Instale PostgreSQL 16." }
}

$dump = Get-ChildItem -LiteralPath (Join-Path $root '.local\backups') -Filter '*.dump' | Sort-Object Name -Descending | Select-Object -First 1
if (-not $dump) { throw 'No hay respaldo .dump en .local\backups.' }

New-Item -ItemType Directory -Force -Path (Join-Path $root '.local') | Out-Null
$pwfile = Join-Path $root '.local\init-password'
try {
    [System.IO.File]::WriteAllText($pwfile, $dbPass)
    & $initdb -D $data -U $dbUser "--pwfile=$pwfile" --auth=scram-sha-256 --encoding=UTF8 --locale=C
    if ($LASTEXITCODE -ne 0) { throw "initdb terminó con código $LASTEXITCODE." }
}
finally {
    if (Test-Path $pwfile) { Remove-Item -LiteralPath $pwfile -Force }
}

$log = Join-Path $root '.local\postgres.log'
& $pgctl -D $data -l $log -o "-h 127.0.0.1 -p $dbPort" start
if ($LASTEXITCODE -ne 0) { throw "pg_ctl no pudo iniciar. Revise .local\postgres.log." }

$env:PGPASSWORD = $dbPass
try {
    & $psql --host 127.0.0.1 --port $dbPort --username $dbUser --dbname postgres --set ON_ERROR_STOP=1 --command "CREATE DATABASE $dbName"
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear la base.' }
    & $restore --host 127.0.0.1 --port $dbPort --username $dbUser --dbname $dbName --no-owner --no-acl --exit-on-error $dump.FullName
    if ($LASTEXITCODE -ne 0) { throw "pg_restore terminó con código $LASTEXITCODE. La base original del respaldo no se modificó; esta copia local quedó para revisión." }
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

Write-Output "Listo. Base restaurada desde $($dump.Name). Contraseñas de acceso: .local\demo-credentials.txt y .local\portal-demo-credentials.txt. No se mostraron secretos."
