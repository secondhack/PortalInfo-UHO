# PortalInfo UHO · Entrega local

Aplicación para demostrar en una tesis la gestión de contenidos del Portal Cautivo de la Universidad de Holguín. Django/DRF y PostgreSQL implementan negocio, seguridad y persistencia; React administra; el portal HTML5/JavaScript nativo consume contenidos, votos y vistas reales. Las identidades y la autorización de red son exclusivamente DEMO.

**Todo permanece local. No se publica en GitHub/GitLab ni se conectan cuentas externas.** No se contactan AGA_AUTH, pfSense, SMTP institucional, SIGENU o ASSET ni se concede acceso a Internet.

**Excepción de revisión:** hay una copia en un repositorio **privado** de GitHub, compartida solo con el tutor. No cambiarla a pública. El `.env` y las cuentas demo siguen siendo locales y ficticias; no van en capturas ni en la memoria. Cómo levantarlo en otro equipo: [PARA_EL_TUTOR.md](PARA_EL_TUTOR.md).

## Empezar desde VS Code

Abre esta carpeta en VS Code y sigue [la guía paso a paso](docs/manuales/COMO_PROBAR_EN_VSCODE.md). En este equipo .env, .venv, PostgreSQL y las cuentas ficticias ya están preparados. No repitas bootstrap ni recrees la base.

Desde la raíz, primero comprueba:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verificar_entorno.ps1
```

Terminal 1:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_backend.ps1
```

Terminal 2:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_frontend.ps1
```

Terminal 3:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_portal.ps1
```

El portal lo sirve Django: no se inicia un tercer servidor. Bypass afecta solo al proceso, no cambia políticas globales. Los scripts no necesitan privilegios de administrador. Alternativas directas: `.venv\Scripts\python.exe -u scripts\serve_backend.py`, `npm.cmd --prefix frontend run dev` y abrir /portal/. Detener los dos servidores con Ctrl+C.

| Interfaz | Dirección |
|---|---|
| Administración React | http://127.0.0.1:5174 |
| Portal cautivo | http://127.0.0.1:8010/portal/ |
| Estado de Django/PostgreSQL | http://127.0.0.1:8010/api/health/ |
| Swagger local | http://127.0.0.1:8010/api/docs/ |

PostgreSQL del proyecto usa 127.0.0.1:55432 y .local/postgres. Se conservan servicios ajenos 8000/5173/5432. Si el clúster del proyecto está detenido: scripts\start-database.cmd; no reiniciar una instancia activa.

## Cuentas ficticias y datos

Credenciales CMS: .local/demo-credentials.txt (Superadmin/Admin/Gestor). Visitantes: .local/portal-demo-credentials.txt. No imprimir, publicar ni mostrar esos archivos o .env en capturas. Para instalación nueva: `backend/manage.py seed_demo` y `seed_portal_demo`, mediante el Python de .venv. Las semillas conservan cuentas/contraseñas existentes.

El Gestor necesita categoría asignada y concesión por operación. Guarda borrador, envía, el Admin recibe notificación y aprueba; la API/portal muestran la publicación. Editar como Gestor conserva la versión pública anterior hasta nueva aprobación. Encuestas, gráficos, resultados y CSV/PDF utilizan datos de PostgreSQL. Correo demo se guarda en .local/mail cuando se activa esa preferencia.

## Verificar la entrega

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\probar_sistema.ps1
# Con backend iniciado: usuario nuevo, dos aprobaciones, encuesta y doce exportaciones
.\.venv\Scripts\python.exe scripts\smoke_final_http.py
# Carga solo local: tasa/duración/conexiones acotadas; no desactiva cuotas
.\.venv\Scripts\python.exe scripts\medir_rendimiento_final.py --connections 200 --rate 5 --seconds 5
# Respaldo nuevo y catálogo validado, sin sobrescritura
.\.venv\Scripts\python.exe scripts\respaldar_base.py
```

Resultado final: **173 pruebas aprobadas, 0 fallidas** (118 backend, 26 React, 17 portal/DOM y 12 navegador). Las suites funcionales y la carga se informan separadamente en [RESULTADOS.md](docs/pruebas/RESULTADOS.md). El script conserva test_portalinfo reutilizable con --keepdb; los tests necesitan CREATEDB de desarrollo y no reinician PostgreSQL. El smoke crea datos propios, los retira lógicamente/desactiva y conserva historial; no edita contenido ajeno. El comprobador de secretos compara valores locales sin mostrarlos.

Portal final: captive-portal/dist/index.html, **24539 bytes sin gzip**, límite 204800. `node captive-portal/build.mjs` compila CSS/JS inline; `scripts/check_portal_size.py` verifica independientemente. Estilos propios compatibles con subconjunto Bootstrap 5, sin distribución completa ni JS de Bootstrap. Sin React/CDN/fuentes externas/imágenes/videos/adjuntos en el portal.

Waitress local: ocho hilos, cola/conexiones acotadas; PostgreSQL reutiliza conexiones hasta 60 s con comprobación de salud, configurable DATABASE_CONN_MAX_AGE. La ráfaga HTML de 200 respondió correctamente; la API conserva 429 al exceder 120/min/IP. Las medidas loopback no certifican WiFi, carga móvil de 1–2 s ni rendimiento institucional. Se conservan resultados negativos previos de runserver.

## Documentación

- [Instalación nueva](docs/manuales/INSTALACION.md), [guía VS Code](docs/manuales/COMO_PROBAR_EN_VSCODE.md) y [uso](docs/manuales/USO.md).
- [Superadmin](docs/manuales/SUPERADMIN.md), [Admin](docs/manuales/ADMIN.md), [Gestor](docs/manuales/GESTOR.md) y [Portal cautivo](docs/manuales/PORTAL_CAUTIVO.md).
- [Mantenimiento/respaldo/restauración segura](docs/manuales/MANTENIMIENTO.md) y [despliegue orientativo](docs/manuales/DESPLIEGUE_ORIENTATIVO.md).
- [Entrega final](docs/arquitectura/ENTREGA_FINAL.md), [arquitectura](docs/arquitectura/ARQUITECTURA.md), [modelo](docs/arquitectura/MODELO_DATOS.md), [permisos](docs/arquitectura/PERMISOS.md) y [contratos API](docs/arquitectura/CONTRATOS.md).
- [Trazabilidad de 84 requisitos originales](docs/arquitectura/TRAZABILIDAD.md), [auditoría](docs/pruebas/AUDITORIA_FINAL.md), [resultados](docs/pruebas/RESULTADOS.md) y [pendientes](docs/arquitectura/TODO.md).

Docker Compose y Nginx/Gunicorn se conservan como material técnico orientativo; no se usa Docker en la demostración ni se acredita despliegue real. Integraciones institucionales, TLS/restore real y aceptación de dispositivos/identidad visual requieren validación autorizada. RNF-16 queda pendiente por decisión del usuario, sin repositorio remoto ni pipeline.