# Auditoría final de la entrega local

Se contrastaron código, modelos/migraciones, rutas/serializers/permisos, páginas React, portal fuente/artefacto, tests y documentos de bloques previos. Se releyó el SRS original de 24 folios y el mockup, conservando archivos originales. Los nombres REQUERIMIENTOS.pdf/MOCKUP.html del encargo son alias de los dos archivos con nombre completo existentes en docs/requisitos.

| Área | Estado comprobado y evidencia | Hallazgo/corrección o limitación |
|---|---|---|
| Autenticación CMS | Login/logout/allowlist/roles y CSRF; SecurityTests + flujo HTTP real | Presupuesto de fallos por IP serializado con bloqueo PostgreSQL, Retry-After y entradas acotadas; no-store en respuestas privadas |
| Visitantes | Sesión aparte del CMS, cookie anterior inválida, vencimiento/revocación y CSRF; PortalTests | AGA_AUTH/pfSense no disponibles; demo nunca concede Internet |
| Usuarios y permisos | CRUD, Superadmin protegido, asignación y concesiones; SecurityTests y Gestor nuevo creado por API | No se modifica ningún usuario previo para comprobar; usuario HTTP propio se desactiva conservando historial |
| CMS de seis tipos | Núcleo editorial, API y formularios; ContentTests, React y smoke | La vigencia predeterminada era configurable pero no se consumía: ahora se aplica a nuevos contenidos; ediciones preservan fechas |
| Aprobaciones | Propuesta congelada, decisión transaccional, segunda revisión conserva versión pública; tests y HTTP | No duplicación con concurrencia/reintentos; rechazo exige motivo |
| Notificaciones/correo | Inbox aislado, contador/lectura, eventos y salida/reintentos; AdministrationTests + correo local HTTP | SMTP institucional pendiente; preferencia temporal del smoke restaurada si no hubo cambio ajeno |
| Analítica y reportes | ORM, períodos, logs, señales y seis CSV/PDF; tests + doce exportaciones HTTP analizadas | Se corrige rango de fechas extremo que podía desbordar; señales no bloquean automáticamente |
| Portal | HTML 24370 bytes, sin CDN, contenido/votos/vistas reales, timeout editorial independiente y XHR; PortalTests y 17 DOM | Orígenes de auth/API distintos se rechazan en build porque la demo usa sesión/CSRF de origen compartido |
| React | Todas las rutas/components existentes examinados y pruebas/build ejecutados | Protección contra respuestas tardías en listados; diálogos reutilizados con foco/Escape y callback de cierre vigente; errores de conexión comprensibles |
| PostgreSQL | Conectado, 36 migraciones al día, restricciones/índices/transacciones existentes conservados | Sin SQLite, resets o migraciones nuevas. Respaldo pg_dump creado y catálogo validado; restauración real pendiente |
| Windows | Cinco scripts pedidos más helper compartido, entorno/base/dependencias/puertos y alternativas directas | Bypass solo por proceso; no requiere admin ni cambia política global. Codex necesitó lectura fuera del sandbox para optimizar Vite |
| Rendimiento | Nuevo servidor local Waitress, cola/hilos limitados; JSON reproducible | HTML 200/200, API 60/200 correctas y 140 cuotas 429 en ráfaga; no se certifica RNF-03 institucional ni latencia móvil |
| Seguridad/secretos | ORM/escape/URL/CSRF/permisos/exportaciones y escaneo de valores locales sin divulgarlos | Producción rechaza demo/DEBUG/clave placeholder. No es auditoría externa ni certificación de ausencia de vulnerabilidades |
| Integraciones/remoto | Adaptadores separados y guía de despliegue | AGA_AUTH/pfSense/SMTP/SIGENU/ASSET pendientes; RNF-16 pendiente por decisión explícita; no se publica nada |

Las comprobaciones de navegador terminaron: 12 aprobadas en Chrome 157.0.8103.39, con 18 rutas del panel, pestañas, formularios móviles, cinco anchos del portal, teclado, permisos, fallo editorial, encuesta y descargas reales. Se revisaron capturas representativas; el conjunto permanece en .local/capturas. RESULTADOS.md y NAVEGADOR_FINAL.json detallan alcance. No se certifican dispositivos físicos ni WCAG completo. Las pruebas funcionales y la carga se informan por separado, conservando resultados negativos anteriores.
