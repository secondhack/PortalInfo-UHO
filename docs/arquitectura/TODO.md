# Estado final · PortalInfo UHO exclusivamente local

Bloques 1–5 cerrados para demostración local en Windows/VS Code. **173 pruebas automatizadas aprobadas, 0 fallidas/omitidas:** 118 backend, 26 React, 17 portal/DOM y 12 Chrome/Playwright. Otras 29 comprobaciones HTTP reales correctas, sin contarlas como tests adicionales. Build, OpenAPI, dependencias, scripts y migraciones comprobados. Informe completo: ENTREGA_FINAL.md; evidencia: docs/pruebas/RESULTADOS.md y JSON finales.

## Entrega completada

- Backend Django/DRF/PostgreSQL, CMS React y portal HTML5/JS independientes, con roles/concesiones, CRUD, publicaciones/versiones/cola, notificaciones/correo local, encuestas/resultados, estadísticas/logs/señales/auditoría/reportes y API pública.
- Flujo HTTP completo: Gestor nuevo por API, permisos, noticia borrador/solicitud/aprobación/vista/dashboard, edición preservando versión pública, reaprobación y encuesta/exportaciones. Solo datos propios de comprobación retirados lógicamente/desactivados, conservando historial/respuestas.
- Seguridad: intentos concurrentes coordinados por IP en PostgreSQL, CSRF, Cache-Control privado, entradas/fechas acotadas, APP_ENV desconocido rechazado, demo/DEBUG/clave insegura bloqueados en producción, secretos fuera de fuentes/HTML.
- Vigencia predeterminada configurada efectiva, respuestas tardías React ignoradas, diálogos/foco/Escape/errores corregidos; tablas móviles/etiquetas/identificación WiFi mejoradas.
- Portal final captive-portal/dist/index.html: 24539 bytes sin gzip, máximo 204800. Sin CDN/React/medios adjuntos. CSS propio compatible con subconjunto Bootstrap 5, no distribución completa.
- Waitress local en 8010, ocho hilos y cola/conexiones acotadas. PostgreSQL reutiliza conexiones hasta 60 s con health checks. No se reinició el clúster.
- Scripts verificar_entorno.ps1, iniciar_backend.ps1, iniciar_frontend.ps1, iniciar_portal.ps1 y probar_sistema.ps1 comprobados. Portal servido por Django: no hace falta tercer servidor. Bypass solo por proceso, sin admin ni cambio global de política.
- Chrome 157.0.8103.39 localizado en Program Files (x86), perfil temporal en .local; 18 rutas/pestañas/formularios y portal 360/390/480/768/1280, permisos, teclado, API editorial caída, encuesta real y descargas. Capturas privadas .local/capturas. Descarga adicional detenida al localizar navegador existente.
- 36 migraciones existentes conservadas, ninguna nueva/destructiva. test_portalinfo separada conservada con --keepdb; los tests concurrentes cierran sus conexiones explícitamente.
- Respaldo privado pg_dump creado y catálogo validado; restaurar_base_nueva.py rechaza la base actual/destinos existentes. No se ejecutó restauración real ni retención/borrado físico.
- Documentación, guía VS Code, manuales por rol/instalación/portal/mantenimiento/despliegue, OpenAPI y matriz de 84 requisitos con estados/evidencia/pruebas/limitaciones actualizados.

## Pendientes reales de aceptación institucional

1. Contratos/servicios autorizados AGA_AUTH/pfSense/SMTP/SIGENU/ASSET. No inventar URLs/protocolos ni sustituir integración por demo; nunca modificar redes o conceder Internet sin autorización/contrato.
2. TLS/Docker/Linux/Nginx/Gunicorn, caché compartida entre workers, usuarios DB mínimos, programación/monitoreo y recuperación desde respaldo en otra base nueva.
3. Carga institucional sostenida/multiusuario/IP y renderizado en WiFi real. La medición final loopback dio HTML 200/200; API 60 HTTP 200 y 140 cuotas 429 en ráfaga. Picos activos medidos 194/199, no se redondean a 200 simultáneos. RNF-03 parcial; no desactivar seguridad para fabricar un resultado favorable.
4. Dispositivos Android/iOS/WebViews físicos, lector de pantalla/contraste/zoom exhaustivos, WCAG completo y Manual de Identidad oficial. Chrome local no certifica esos entornos.
5. RNF-16 (repositorio remoto) pendiente por decisión expresa del usuario. **No publicar, no git push, no GitHub CLI, no pipelines ni cuentas externas.** Toda la entrega sigue local.

## Para retomar o demostrar

Leer README y docs/manuales/COMO_PROBAR_EN_VSCODE.md. No repetir bootstrap_database, recrear la base, borrar tablas/migraciones ni reiniciar PostgreSQL activo. Puertos propios: 8010/5174/55432; se conservan 8000/5173/5432 ajenos.

Credenciales CMS/visitantes en .local/demo-credentials.txt y .local/portal-demo-credentials.txt; no imprimirlas ni publicarlas. seed_demo/seed_portal_demo son idempotentes. Los servidores QA propios se detienen al terminar; PostgreSQL/datos/respaldos se conservan. Las incidencias iniciales de runserver, cierre de conexiones y sandbox se documentan sin ocultarlas.