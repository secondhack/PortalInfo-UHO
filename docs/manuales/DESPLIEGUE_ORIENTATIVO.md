# Despliegue orientativo · no ejecutado

La demostración validada usa Windows, PostgreSQL local, Waitress en 8010 y Vite en 5174, sin Docker. Estos pasos describen una futura instalación autorizada; no implican publicación ni integración institucional operativa.

- Django: requirements-production.txt incorpora Gunicorn para Linux; desde backend, `gunicorn -c ../scripts/gunicorn.conf.py config.wsgi`. Dos workers y cuatro hilos, cola 256; dimensionar con mediciones y PostgreSQL. No utilizar runserver en producción.
- PostgreSQL: base persistente, usuario de aplicación restringido, usuario de migración separado y respaldos/restore probados. No compartir secretos ni exponer 5432/55432 públicamente.
- React: `npm.cmd --prefix frontend run build`; servir frontend/dist con Nginx, fallback a index.html para rutas SPA. No hace falta Node en ejecución de esos archivos.
- Portal: construir captive-portal/dist/index.html y conservar origen/proxy común para /api/ y /portal-auth/. Django /portal/ sirve la demo; para pfSense se necesita el contrato de autenticación/red y validación de cookies/CSP/TLS.
- Nginx: scripts/nginx.example.conf describe rutas reales de la instalación local. Para producción deben añadirse hostname/certificados autorizados, redirección HTTPS y un proxy que elimine cabeceras entrantes no confiables. Configurar el reconocimiento HTTPS de Django solo cuando ese proxy esté controlado; no confiar indiscriminadamente en X-Forwarded-Proto.
- Django production: APP_ENV=production, PORTALINFO_DEBUG=false, AUTH_PROVIDER=aga, PORTAL_AUTH_MODE=institutional, SECRET_KEY propia y larga, ALLOWED_HOSTS explícitos. Cookies Secure/HSTS/redirect HTTPS están preparados; sin reconocimiento correcto del proxy TLS puede producirse un bucle de redirección y debe resolverse antes de desplegar. AGA_AUTH sigue devolviendo 503 sin contrato, no se habilita demo como sustituto.
- CORS/CSRF: preferir mismo origen. Si se autoriza otro origen, añadirlo explícitamente en PORTAL_ALLOWED_ORIGINS y comprobar SameSite, dominio de cookies y CSP. El build rechaza bases de autenticación/API diferentes en esta demo para evitar una configuración CSRF incompleta.
- Caché: la demostración usa caché local en un proceso. Antes de múltiples workers usar un backend compartido para cuotas. Los intentos de login también se coordinan mediante PostgreSQL, pero eso no convierte el throttling general en distribuido.
- SMTP: únicamente con contrato/credenciales explícitos y EMAIL_MODE=smtp fuera de demo. La salida persistente conserva la limitación de entrega al menos una vez ante caída después de aceptación SMTP.

Docker Compose se conserva como entregable técnico de desarrollo. Monta el HTML de portal como solo lectura, publica backend/frontend solo en loopback y mantiene volumen PostgreSQL. No se ha ejecutado Docker aquí ni debe utilizarse para la defensa local. No ejecutar docker compose down -v ni reemplazar el clúster existente.

Programación de tareas, observabilidad, pruebas de carga con varios usuarios/IP, verificación TLS, restauración y revisión de accesibilidad/dispositivos son pasos de aceptación pendientes. RNF-16 permanece pendiente por decisión del usuario: no se crea repositorio remoto ni pipeline, no se usa GitHub CLI y no se sube la entrega a ningún servicio.
