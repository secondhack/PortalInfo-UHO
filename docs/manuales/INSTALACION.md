# Instalación local en Windows

En este equipo el proyecto ya está configurado: usa COMO_PROBAR_EN_VSCODE.md. No repitas bootstrap ni recrees PostgreSQL sobre una instalación existente.

En un equipo nuevo se necesitan Python 3.11+, Node 22.12+ (validado Node 24.16), PostgreSQL 16 y sus herramientas pg_dump/pg_restore. Los scripts no necesitan privilegios de administrador; la instalación de herramientas depende de la política del equipo. No se usa Docker para la demostración.

Abre la carpeta PortalInfo-UHO en VS Code. Desde su raíz:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
npm.cmd --prefix frontend ci --no-audit --no-fund --cache .local/npm-cache
```

backend/requirements.lock.txt fija versiones de ejecución validadas; requirements-dev añade pypdf para pruebas. Waitress es el servidor local Windows. Playwright es solo herramienta de pruebas visuales; no forma parte del portal final.

Si todavía no existe .env, copia .env.example con un nombre .env y sustituye SECRET_KEY/credenciales por valores aleatorios propios. Nunca sobrescribas un .env válido ni uses los placeholders de ejemplo. `scripts/bootstrap_database.py` es la alternativa automatizada para una instalación local completamente nueva: genera secretos y el clúster privado .local/postgres en 55432; requiere herramientas PostgreSQL 16. Inspecciona el script antes de ejecutarlo y no lo uses en este equipo ya inicializado.

Para PostgreSQL local nuevo ya configurado en .env:

```powershell
.\scripts\start-database.cmd
.\.venv\Scripts\python.exe scripts\create_database.py
.\.venv\Scripts\python.exe backend\manage.py showmigrations
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py seed_demo
.\.venv\Scripts\python.exe backend\manage.py seed_portal_demo
node captive-portal/build.mjs
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verificar_entorno.ps1
```

create_database conserva bases existentes; migrate aplica incrementales. No ejecutar flush, borrar tablas/migraciones ni sustituir PostgreSQL por SQLite. El usuario DB de desarrollo necesita CREATEDB para tests; para producción debe limitarse y diseñarse un usuario de migración separado.

Las contraseñas ficticias se crean únicamente en .local/demo-credentials.txt y portal-demo-credentials.txt. Las semillas no reemplazan cuentas existentes. Inicia las terminales con la guía de VS Code. No modificar la política global PowerShell: Bypass por proceso o comandos directos.

Las pruebas detectan Chrome local en Program Files/Program Files (x86), con un perfil de prueba aislado bajo .local/browser-temp; no usan tu perfil habitual. PORTAL_BROWSER_EXECUTABLE permite indicar otro Chrome/Chromium compatible. Si no tienes navegador compatible, puedes instalar el de Playwright dentro del proyecto:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.local/ms-playwright'
.\frontend\node_modules\.bin\playwright.cmd install chromium
```

No se requiere para usar el CMS/portal. Mantener navegador, cachés, respaldos y credenciales en .local, excluido de entregables públicos. No se publica ni conecta a servicios de alojamiento.

Con backend y frontend iniciados: `.\frontend\node_modules\.bin\playwright.cmd test --config frontend/playwright.config.js`. La entrega se verificó con Chrome 157.0.8103.39 instalado en Program Files (x86); se detuvo la descarga adicional al localizarlo. No se instala un servicio ni se abre el perfil del usuario.
