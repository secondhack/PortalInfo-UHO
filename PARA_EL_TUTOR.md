# Para el tutor

Copia privada para revisar la tesis. No haga público este repositorio.

Incluye lo necesario para entrar y ver los mismos datos de la demo:

- `.env` (clave local de Django y usuario/contraseña del PostgreSQL del proyecto; no hay SMTP ni cuentas institucionales)
- `.local/demo-credentials.txt` (Superadmin, Admin y Gestor)
- `.local/portal-demo-credentials.txt` (visitantes del portal)
- `.local/backups/*.dump` (respaldo de la base ya sembrada)
- `.local/capturas/` (evidencia de pantallas)

No incluye `node_modules`, el entorno `.venv` ni la carpeta de datos `.local/postgres`. Eso es de la PC donde se desarrolló (Windows) y no arranca en otro equipo. Se reconstruye aquí.

## Equipo nuevo (Windows)

Hace falta Python 3.11+, Node.js 22.12+ y PostgreSQL 16, con `bin` en `C:\Program Files\PostgreSQL\16\bin`.

En PowerShell, desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
npm.cmd --prefix frontend ci --no-audit --no-fund
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\preparar_equipo_tutor.ps1
```

Ese último script solo corre si **no** existe `.local\postgres`. Crea el clúster con la contraseña que ya está en `.env`, crea la base y restaura el respaldo. No imprime contraseñas. No lo ejecute sobre una instalación que ya tenga datos.

Después, tres terminales, como en el README:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_backend.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_frontend.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_portal.ps1
```

| Interfaz | Dirección |
|---|---|
| Administración | http://127.0.0.1:5174 |
| Portal | http://127.0.0.1:8010/portal/ |
| Salud | http://127.0.0.1:8010/api/health/ |

Los correos y contraseñas están en los dos archivos de `.local` citados arriba. Ábralos solo en su equipo. Si la restauración del respaldo funcionó, **no** vuelva a correr `seed_demo`: generaría otras contraseñas.

Guía completa de uso: [docs/manuales/COMO_PROBAR_EN_VSCODE.md](docs/manuales/COMO_PROBAR_EN_VSCODE.md).
