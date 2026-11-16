# PortalInfo UHO · Informe final de entrega local

## 1. Estado general

Aplicación local funcional y comprobada para demostración de tesis en Windows/VS Code, sin Docker. CMS React, backend Django/DRF, PostgreSQL y portal HTML5/JavaScript nativo separados. Los datos/acciones editoriales, votos, métricas y exportaciones son reales; solo identidad/concesión de red y servicios institucionales se mantienen como DEMO o adaptadores pendientes.

Todo permanece dentro de PortalInfo-UHO. No se usó GitHub CLI, no se creó repositorio remoto/pipeline, no se ejecutó git push ni se publicó/subió el código a ningún servicio. Descargar dependencias de desarrollo no implica publicar la aplicación ni conectar cuentas externas. RNF-16 queda pendiente por decisión expresa del usuario.

## 2. Módulos terminados para demostración

Autenticación CMS y visitantes demo, sesiones/logout/bloqueo, usuarios/roles/concesiones y protección del Superadmin; nomencladores y categorías dinámicas; noticias/eventos/avisos/servicios/encuestas; borrador/envío/cola/aprobación/rechazo/versiones/vigencia/visibilidad; campana/contador/lectura/correo local; dashboard/logs/alertas/resultados/gráficos/CSV/PDF/auditoría; API pública y portal nativo con error/timeout editorial independiente del login.

El flujo integral crea un Gestor mediante API, asigna permisos, publica una noticia, registra una vista, edita como Gestor preservando la publicación anterior y aprueba la revisión nueva. Una encuesta propia se publica, responde y exporta desde datos persistidos. No hay intervención manual en PostgreSQL para realizar esos flujos.

## 3. Pendientes y límites

AGA_AUTH/pfSense/SMTP/SIGENU/ASSET reales dependen de contratos/servicios autorizados y no se invocan. No se concede Internet ni se modifican redes. TLS, Docker/Linux/Nginx/Gunicorn, restauración real, caché compartida y carga institucional multiusuario/IP no están certificados. Chrome local verifica geometría/teclado en los anchos ensayados, no dispositivos Android/iOS físicos, WebViews ni cumplimiento completo WCAG/Manual de Identidad. No se presenta la entrega como despliegue institucional.

## 4. Correcciones realizadas

- Login CMS coordinado por IP con bloqueo asesor transaccional PostgreSQL, Retry-After y tamaño de entrada acotado; padding para usuario desconocido sin crear identidades.
- Respuestas privadas con Cache-Control no-store y auditoría de denegaciones del portal; producción rechaza demo/DEBUG/clave placeholder o corta y APP_ENV desconocido no activa demo.
- La vigencia predeterminada configurable ahora se aplica a nuevos contenidos; se transforma en rango custom sin cambiar fechas anteriores ni añadir migraciones. Se acotan días y fechas extremas que podían desbordar.
- Logout puede cerrar una sesión ya inválida sin omitir CSRF; un error de carga termina el indicador de espera. Listados React ignoran respuestas tardías; diálogos de recursos usan foco/Escape y callback vigente; errores de conexión comprensibles. Etiquetas DEMO/estados y tablas móviles corregidas.
- Identificación WiFi visible también en móvil. El build rechaza bases auth/API diferentes para no entregar una configuración de sesión/CSRF incompleta.
- Waitress reemplaza runserver como arranque local, con ocho hilos/cola limitada. Conexiones PostgreSQL reutilizables hasta 60 s y health checks reducen el coste por petición sin ampliar indefinidamente conexiones.
- La reutilización de conexiones reveló dos sesiones abiertas en tests concurrentes al retirar test_portalinfo. Se corrigió cierre explícito por hilo; probar_sistema conserva además la base separada con --keepdb, sin borrar bases de trabajo. La incidencia anterior se conserva en los resultados.
- Detección de Chrome ampliada a Program Files (x86); se utiliza perfil de prueba aislado bajo .local y se detuvo la descarga adicional. La optimización Vite necesitó lectura fuera del sandbox de Codex; en la terminal normal de VS Code no implica un import roto.

## 5. Pruebas y evidencia

**173 pruebas automatizadas aprobadas, 0 fallidas, 0 omitidas en las suites finales:** 118 Django/PostgreSQL, 26 React/Vitest, 17 portal/DOM y 12 Playwright/Chrome. No se suman repeticiones como pruebas distintas. Backend final: 78,012 s; React final: 3,94 s; DOM final: 1,424 s; navegador final: 42,7 s.

Además, scripts/smoke_final_http.py completó **29 comprobaciones HTTP reales**, incluida vigencia configurada, Gestor nuevo, dos aprobaciones, notificación/correo local, voto, dashboard, auditoría y doce exportaciones CSV/PDF analizadas. No se suman esas aserciones al total de tests. E2E_FINAL.json y NAVEGADOR_FINAL.json contienen evidencia; RESULTADOS.md conserva historial/incidencias.

Playwright comprobó 18 rutas administrativas y pestañas de estadísticas sin excepciones JavaScript ni API administrativas fallidas, formularios móviles y permisos, portal sin desbordamiento a 360/390/480/768/1280 px, WiFi visible, teclado/foco, autenticación con API editorial bloqueada, encuesta desde formulario hasta PostgreSQL/resultados y descargas reales. Se revisaron capturas representativas de panel/portal/tablas/formularios; capturas de todas las rutas están en .local/capturas, sin subirlas a ningún servicio. Chrome utilizado: 157.0.8103.39; perfiles de usuario habituales intactos.

No ejecutadas: aceptación física Android/iOS/WebViews, lector de pantalla/contraste/zoom exhaustivo y certificación WCAG, servicios institucionales, Docker/TLS/despliegue y restauración real. Se omiten por falta de entorno/contrato o porque están fuera de la demostración local autorizada; no figuran como aprobadas.

## 6. Compilación React y dependencias

Build correcto, 61 módulos. JS principal 338,39 kB (104,19 gzip), gráficos 175,37 kB (61,17 gzip), CSS 11,50 kB (3,28 gzip). Solo avisos benignos use client de React Router, sin imports rotos. Dependencias comprobadas con npm ls/pip check; Waitress y Playwright añadidos localmente y reflejados en requirements/package-lock. Playwright no forma parte del runtime del portal.

## 7. PostgreSQL y migraciones

PostgreSQL 16.15 conectado en 127.0.0.1:55432. check, makemigrations --check --dry-run y migrate --check correctos. **36 migraciones aplicadas, sin nuevas migraciones ni cambios destructivos.** No se reinició el clúster, no se usó SQLite ni se borró contenido/base de usuarios. test_portalinfo permanece separada y conservada con --keepdb; los fixtures solo afectan a esa base de pruebas.

Se creó un respaldo privado de 142317 bytes en .local/backups y se validó su catálogo con pg_restore --list. La herramienta de restauración rechaza la base actual y destinos existentes, sin ejecutar una restauración sobre ellos. Una lectura de catálogo no acredita recuperación completa: debe validarse restaurando a otra base nueva en un ejercicio autorizado.

## 8. Portal cautivo final

Ubicación: **captive-portal/dist/index.html**. Tamaño exacto: **24539 bytes sin gzip**, límite 204800. Incluye CSS/JS minificados inline, sin React/CDN/fuentes externas/imágenes/videos/documentos. Usa un subconjunto propio de estilos compatibles con Bootstrap 5, no su distribución completa. build.mjs y check_portal_size.py fallan al exceder el presupuesto.

## 9. Rendimiento medido

Windows 10.0.19041, Intel Family 6 Model 60, cuatro CPU lógicas, Python 3.11.9, Waitress 3.0.2 con ocho hilos/backlog y connection_limit 256, PostgreSQL local con conexiones reutilizables. Cliente http.client + threads/barrera, solo loopback, sin redirecciones ni desactivación de cuotas.

| Prueba final | Resultado |
|---|---|
| API secuencial, cinco muestras por endpoint | Todas HTTP 200; medianas 9,095–34,391 ms; máximo 35,936 ms |
| API a 5 peticiones/s durante 5 s | 25/25 HTTP 200; mediana 22,950 ms, p95 33,281 ms |
| Ráfaga de 200 peticiones al HTML | 200/200 HTTP 200; p95 186,906 ms, máximo 195,938 ms; pico observado 194 peticiones activas |
| Ráfaga de 200 peticiones API | 60 HTTP 200 y 140 HTTP 429 por cuota; máximo de respuestas correctas 409,121 ms; pico observado 199 peticiones activas |

No hubo errores de conexión en la medición final. La barrera programa 200 clientes; los picos reales se informan sin redondearlos a 200 simultáneos. La fase regulada no representa 200 clientes activos a la vez. El límite 120/min/IP permanece: los 429 no se cuentan como éxito funcional de usuarios, ni se ocultan. Latencias de todos los intentos de ráfaga, incluidos 429, pueden superar 500 ms. RNF-03 permanece parcial; esto no certifica carga institucional sostenida ni RNF-01 de renderizado móvil.

RENDIMIENTO_FINAL.json conserva la medición; RENDIMIENTO_WSGI_INICIAL.json y RENDIMIENTO_BLOQUE_4.json conservan resultados anteriores, incluidos los rechazos de runserver. No se sustituyen por métricas inventadas.

## 10. Rutas exactas

| Interfaz | URL |
|---|---|
| React | http://127.0.0.1:5174 |
| Portal cautivo | http://127.0.0.1:8010/portal/ |
| Estado backend/DB | http://127.0.0.1:8010/api/health/ |
| Swagger | http://127.0.0.1:8010/api/docs/ |
| OpenAPI | http://127.0.0.1:8010/api/schema/ |

## 11. Comandos Windows

Desde C:\Users\Darksiders\Desktop\PortalInfo-UHO, comprobar entorno y abrir terminales independientes:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verificar_entorno.ps1
# Terminal 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_backend.ps1
# Terminal 2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_frontend.ps1
# Terminal 3: compila/verifica y deja libre la terminal; no inicia otro servidor
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_portal.ps1
```

No cambiar política global ni ejecutar como administrador. Alternativas directas: `.venv\Scripts\python.exe -u scripts\serve_backend.py` y `npm.cmd --prefix frontend run dev`. Detener solo esos dos servidores con Ctrl+C; conservar PostgreSQL activo. Ver COMO_PROBAR_EN_VSCODE.md para errores frecuentes/instalación.

## 12. Usuarios DEMO

```powershell
.\.venv\Scripts\python.exe backend\manage.py seed_demo
.\.venv\Scripts\python.exe backend\manage.py seed_portal_demo
```

Son idempotentes y no reemplazan contraseñas existentes. Credenciales privadas: .local/demo-credentials.txt y .local/portal-demo-credentials.txt; no se incluyen en código/HTML ni se muestran en informes. Superadmin puede crear otros Gestores/Admins ficticios desde Usuarios, asignar categorías y concesiones. Usuario nuevo con contraseña vacía no tiene acceso demo utilizable. Los visitantes nunca adquieren permisos CMS.

## 13. Guía rápida de noticia y encuesta

Noticia: Superadmin crea Gestor ficticio con Noticias y permisos → Gestor guarda borrador y envía → Admin ve campana/cola, compara y aprueba → Portal Actualizar/Noticias → abrir publicación registra vista → Dashboard Hoy/Interacciones registradas. Editar como Gestor conserva la publicación anterior hasta aprobar la nueva revisión.

Encuesta: Gestor con Encuestas crea preguntas/opciones dentro de límites, guarda/envía → Admin aprueba → visitante abre Encuestas, inicia sesión si se exige y responde → Admin consulta Resultados y descarga CSV/PDF. Borradores/vencidos/ocultos y duplicados se rechazan en Django. Los textos abiertos/resultados no son públicos.

## 14. Documentos y archivos de cierre

Cinco scripts pedidos de Windows más comun.ps1/check_environment.py/serve_backend.py; scripts de respaldo/restauración protegida, escaneo de secretos, medición regulada y smoke integral. Pruebas nuevas en accounts/test_concurrency.py y tests existentes, React/request guard/diálogos y frontend/e2e/local.spec.js. Actualizaciones defensivas/default y CSS móvil, dependencias/locks, configuración orientativa y artefacto HTML.

Manuales: INSTALACION, COMO_PROBAR_EN_VSCODE, SUPERADMIN, ADMIN, GESTOR, PORTAL_CAUTIVO, MANTENIMIENTO y DESPLIEGUE_ORIENTATIVO. Arquitectura/modelo/permisos/contratos/OpenAPI, matriz con 84 IDs/estados/evidencia/pruebas/limitaciones, AUDITORIA_FINAL, RESULTADOS y TODO actualizados. Originales PDF/HTML intactos. Escáner comprueba valores reales de secretos locales sin imprimirlos.

## 15. Confirmación de alcance local

No se publicó nada en GitHub, GitLab ni otros servicios. No se crearon repositorios remotos, GitHub Actions, pipelines o cuentas externas. No se tocaron proyectos ajenos ni servicios institucionales. Se conservan los puertos ajenos 8000/5173/5432. Los servidores QA propios se detienen al terminar; PostgreSQL, datos, respaldos y credenciales locales permanecen.
