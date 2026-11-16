# Mantenimiento local y respaldo

No ejecutar acciones de limpieza destructivas para preparar la tesis. Conservar .env, .local/postgres, credenciales y respaldos privadamente. El proyecto permanece local; no se publica en GitHub/GitLab ni alojamiento remoto.

## Comprobaciones

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verificar_entorno.ps1
.\.venv\Scripts\python.exe backend\manage.py check
.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe backend\manage.py migrate --check
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\probar_sistema.ps1
```

Antes de aplicar migraciones pendientes, inspeccionar showmigrations y el archivo. Hacer respaldo; no borrar tablas/bases/migraciones. Las pruebas del script reutilizan/conservan test_portalinfo mediante --keepdb y requieren CREATEDB de desarrollo. Nunca eliminan la base principal.

## Respaldo PostgreSQL sin sobrescritura

```powershell
.\.venv\Scripts\python.exe scripts\respaldar_base.py
```

Usa pg_dump --format=custom, crea un nombre nuevo en .local/backups y valida el catálogo con pg_restore --list. Lee contraseña de .env y la pasa solo al entorno del proceso hijo; nunca en argumentos/logs. No sobrescribe archivos. PG_BIN permite indicar otra carpeta bin; por defecto busca PostgreSQL 16/PATH. Solo admite servidor local.

Se ejecutó un respaldo y su lectura de catálogo. Eso no equivale a una restauración probada. El dump contiene datos/credenciales hash de demostración: tratarlo como información privada, no adjuntarlo al informe ni publicarlo.

## Restaurar exclusivamente en otra base nueva

Selecciona el nombre real de tu respaldo y un destino inexistente:

```powershell
.\.venv\Scripts\python.exe scripts\restaurar_base_nueva.py --archive .local\backups\NOMBRE_REAL.dump --target portalinfo_revision_nueva
```

La utilidad rechaza la base actual, postgres/template0/template1, cualquier destino existente, nombres inválidos y servidores no locales. Valida el archivo, crea una base nueva y restaura sin --clean/drop. No cambia .env ni reemplaza la base original. Si falla deja la base nueva para diagnóstico; no la elimina automáticamente. Necesita permisos CREATEDB y espacio disponibles. Revisa conteos/integridad y aplicación contra esa copia antes de cualquier cambio manual de entorno. No se ejecutó una restauración real en esta entrega.

## Tareas existentes

```powershell
.\.venv\Scripts\python.exe backend\manage.py register_expirations
.\.venv\Scripts\python.exe backend\manage.py deliver_notifications
.\.venv\Scripts\python.exe backend\manage.py scan_security --period 7d
.\.venv\Scripts\python.exe backend\manage.py maintain_logs
```

La expiración se filtra en cada consulta; el comando registra/notifica una vez. Los reintentos de correo no reenvían entregas ya enviadas. scan_security produce señales, nunca bloquea usuarios. maintain_logs es simulación por defecto. Su aplicación requiere operador autorizado y --apply/--authorized-by/--confirm-days; no se ejecutó sobre datos de trabajo. Programación automática, caché compartida y recuperación de desastres requieren validación en el entorno final.

## Actualizaciones y operación

Detén solo tus servidores con Ctrl+C. Después de cambiar dependencias, instala versiones del lock y ejecuta probar_sistema.ps1. Reconstruye el portal con build.mjs y verifica tamaño; no necesita Node/CDN en ejecución. Copia únicamente artefactos públicos y fuentes autorizadas; excluye .env/.local/.venv/node_modules/capturas con secretos.

Waitress sirve la demo Windows en loopback con ocho hilos y cola 256. Nginx/Gunicorn/Docker siguen como configuraciones orientativas sin despliegue certificado. Producción necesita TLS, claves propias, permisos DB mínimos, caché compartida, backups/restore verificados y contrato institucional real. No activar demo/DEBUG ni correo SMTP real por ensayo.
