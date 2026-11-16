# Aprobaciones, notificaciones y analítica · Bloque 3

Se amplían las aplicaciones existentes, sin reiniciar PostgreSQL ni reemplazar migraciones. Estado inicial ejecutado: 60 pruebas Django/PostgreSQL y 13 React aprobadas. Estado final y evidencia en docs/pruebas/RESULTADOS.md.

## Flujo editorial y concurrencia

Se conservan Content (revisión), Publication (versión aprobada) y Approval. Cada solicitud ahora congela proposal, con los datos exactos presentados. La cola filtra estado, categoría, autor, fechas y título, ordena y pagina. Permite comparar propuesta y última publicación, decidir y consultar historial con responsable/fecha/motivo. Una edición posterior no reescribe el texto de una solicitud histórica.

submit/review vuelven a bloquear la fila Content con SELECT FOR UPDATE dentro de transacción, incluso al invocarlos desde otro servicio. Se revisa la versión antes de decidir. Dos administradores concurrentes no publican dos veces: uno decide y el otro recibe 400 si la solicitud dejó de estar pendiente. Un reintento idéntico del mismo administrador devuelve el resultado previo sin nueva publicación, auditoría ni notificación. Enviar otra vez la misma revisión pendiente tampoco duplica solicitudes.

Las ediciones del Gestor requieren nuevo envío y conservan intacta la versión pública anterior aprobada. Admin puede corregir directamente una publicación aprobada. Aprobar nunca habilita una sección, cambia el switch ni extiende fechas. El núcleo del Bloque 2 sigue siendo la única lógica editorial; el endpoint de cola delega en él.

La migración congela propuestas históricas solo cuando la revisión actual o una Publication permiten reconstruirlas con certeza. No se inventan propuestas de revisiones desconocidas. Las notificaciones antiguas sin referencia/fecha de lectura se conservan; los eventos nuevos siempre registran referencia y lectura cuando ocurre.

## Notificaciones y correo

Notification añade título, tipo/referencia, read_at, indicador DEMO y event_key. La restricción destinatario/event_key garantiza idempotencia. El envío a aprobación notifica a Admin/Superadmin activos y autorizados; aprobación/rechazo y expiración notifican al autor. Rechazar exige motivo y lo incluye en el mensaje. La expiración sigue siendo idempotente por Publication.

Cada usuario solo puede listar/consultar/marcar sus propias notificaciones. La campana consulta el contador cada 30 segundos mientras la pestaña está visible; al abrir muestra el listado y ofrece lectura individual/colectiva. /notifications permite paginar. El enlace /contents?content=ID abre el detalle y vuelve a aplicar permisos de categoría. No existe borrado de notificaciones por API.

MailDelivery es una salida persistente OneToOne, con estado, intentos y fecha. Se crea junto al evento cuando email_notifications está habilitado y el destinatario mantiene acceso. El envío se ejecuta tras commit, mediante el backend Django. Un fallo de correo no deshace una aprobación; queda reintentable y solo registra el nombre de la excepción, sin credenciales/cuerpos SMTP. Las plantillas de texto y HTML son comunes a los eventos y escapan contenido dinámico.

EMAIL_MODE=file (predeterminado) escribe en .local/mail; console y memory también son proveedores demo. La demostración rechaza EMAIL_MODE=smtp. Producción admite smtp solo con EMAIL_HOST explícito y variables EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS y DEFAULT_FROM_EMAIL. No se inventa ningún host/credencial institucional ni se envían correos reales en esta entrega. El remitente ficticio predeterminado utiliza example.invalid.

Activar el correo no reenvía notificaciones históricas: se aplica a eventos nuevos. `python backend/manage.py deliver_notifications --limit 100` procesa pendientes/fallidos; omite los enviados. La idempotencia de eventos y reintentos ordinarios está verificada. Ante una caída entre aceptación SMTP y persistencia del estado existe la limitación habitual de entrega al menos una vez; no se afirma exactamente una vez para un SMTP real aún no integrado.

## Registro de actividad e identidad

POST /api/vistas solo acepta {section, content?}. Rechaza campos adicionales de identidad. Valida sección activa/visible y, si hay contenido, su publicación efectiva y pertenencia a la sección, incluido el límite máximo. Requiere CSRF también para visitantes anónimos y limita a 60 solicitudes/minuto/IP.

La IP y User-Agent provienen del contexto de solicitud. Se ignora X-Forwarded-For salvo que REMOTE_ADDR pertenezca a TRUSTED_PROXY_CIDRS; entonces se recorre la cadena de derecha a izquierda hasta el primer salto no confiable. Se limita longitud/cantidad de saltos y se validan direcciones. NUM_PROXIES=0 mantiene el rate limiting general conservador. El despliegue debe configurar únicamente sus proxies reales, nunca redes abiertas indiscriminadamente.

La identidad es un HMAC de la identidad verificada por el servidor o de la sesión CMS, sin almacenar correo/DNI. Una sesión demo se etiqueta como demo; un visitante anónimo no recibe identidad persistente. VerifiedPortalIdentity es un contrato interno para un proveedor confiable futuro, no un objeto recibido por JSON. La integración AGA_AUTH/pfSense permanece pendiente.

POST /api/demo/portal-access/ registra un acceso de prueba usando exclusivamente la sesión demo autorizada. No acepta una identidad del navegador, no autentica en pfSense y no concede Internet. Los logins del CMS se auditan como administrativos y no inflan los accesos al portal.

AccessLog distingue access y view; ContentView enlaza su AccessLog y conserva categoría, identidad seudónima y tipo aplicables. No se suman las dos tablas para contar dos veces una visualización. Dispositivo es una clasificación limitada de User-Agent (mobile/tablet/desktop/bot/unknown), no identificación fiable del hardware.

## Métricas y resultados

Los contadores/agregados proceden de PostgreSQL mediante Count, filtros y truncado/extracción temporal. No hay cifras del mockup. /api/admin/dashboard/ conserva las claves anteriores y añade activos/no visibles, solicitudes, categorías/estados, creados en período, accesos, vistas, envíos de encuestas y contenidos más vistos. Los totales de contenido son la fotografía actual; actividad y creados_in_period usan el período.

/api/admin/estadisticas devuelve accesos por día/semana/mes, tipo de usuario/dispositivo/hora, visualizaciones por día/sección/categoría y top de contenidos. Admin/Superadmin puede consultar métricas globales y logs; el Gestor solo ve contadores y contenidos de sus categorías, sin accesos globales ni datos restringidos.

| Período | Calendario del servidor, America/Havana |
|---|---|
| today | Día local completo |
| 7d / 30d | Siete/treinta días calendario, incluyendo hoy |
| month | Desde el primer día del mes hasta el final de hoy |
| custom | date_from/date_to inclusivas en el formulario, convertidas a [inicio, medianoche siguiente al fin) |

Las semanas del agregado comienzan en lunes. La respuesta incluye límites y zona. data_scope=real (predeterminado) significa interacciones registradas, no semilla; demo selecciona ejemplos ficticios y all los incluye explícitamente. Los datos de contenidos del CMS no se borran por cambiar esta fuente, y demo_contents informa de sus ejemplos. No se equiparan interacciones locales con tráfico institucional.

Resultados de encuestas: se agregan envíos, identidades seudónimas distintas y respuestas por versión/pregunta/opción. Una identidad puede enviar en varias versiones; no equivale a personas únicas. La selección múltiple puede sumar más del 100 %. Los resultados incluyen la cantidad DEMO. El endpoint previo sin filtros conserva la consulta histórica; con período/fuente aplica sus filtros.

Los textos abiertos solo son accesibles a Admin/Superadmin. El resumen incluye como máximo 100 por pregunta y marca truncamiento; open_answers/ pagina la consulta completa. Los reportes autorizados permiten exportarlos. Las consultas estadísticas no cargan todos los votos en memoria para calcular conteos.

Chart.js se integra por componentes registrados y se empaqueta en un chunk separado; las tablas alternativas exponen los mismos datos para accesibilidad. Se usan gráficos de línea, barras y distribución, con estados vacíos, carga y error. Referencia primaria: [integración oficial de Chart.js](https://www.chartjs.org/docs/latest/getting-started/integration.html).

## Señales defensivas

SecurityAlert registra identidad seudónima, tipo, prioridad, ventana, evidencia resumida, indicador DEMO y revisión humana. Las reglas solo analizan accesos con identidad del servidor, no vistas anónimas arbitrarias:

- Varias IP: al menos security_ip_threshold direcciones distintas por ventana.
- Cambios de dispositivo: al menos security_device_threshold User-Agent distintos; no se afirma que correspondan a equipos físicos diferentes.
- Actividad inusual: mínimo security_activity_threshold accesos y factor security_activity_multiplier respecto a la ventana inmediatamente anterior, solo si existe historia previa.

security_window_minutes define ventanas alineadas en UTC; la interfaz presenta fechas en America/Havana. La lista/reportes incluyen ventanas que intersectan el período. Los umbrales se modifican por Superadmin desde Configuración. La clave única por identidad/regla/ventana/fuente impide duplicados por reanálisis. Se preserva la primera evidencia detectada y su revisión; no se reescriben decisiones humanas al repetir el análisis.

Las señales son indicios, no prueba de uso compartido: NAT, navegadores actualizados o cambios de red pueden explicarlas. No bloquean cuentas automáticamente. La interfaz permite filtrar prioridad/fecha/estado, ver evidencia y marcar revisada. `scan_security` automatiza el mismo servicio de análisis.

## Auditoría, privacidad y retención

Se conservan los eventos previos y se añade entity. Usuarios/roles/permisos/configuración/contenido registran resúmenes antes/después de campos permitidos; no se almacenan contraseñas/tokens ni cuerpos SMTP. La pantalla filtra actor, acción, entidad, fecha y búsqueda, pagina y muestra detalle. Solo Superadmin consulta/exporta la auditoría global. No hay métodos de actualización/eliminación administrativa de logs/auditoría.

`python backend/manage.py maintain_logs` simula la política retention_days. Aplicar exige un operador autorizado, --apply, --authorized-by ID de Superadmin activo/autorizado y --confirm-days igual a la política vigente. Solo elimina AccessLog, ContentView, SecurityAlert y AuditEvent anteriores al corte; registra retention.applied con conteos. No elimina usuarios, contenidos, publicaciones, encuestas ni respuestas.

En esta entrega se ejecutó únicamente simulación sobre la base de trabajo. La aplicación de retención se probó exclusivamente en la base efímera de tests. El identificador de autorización deja trazabilidad del operador; no sustituye el control de acceso del sistema operativo para ejecutar comandos de mantenimiento. Correo demo en disco requiere una política de archivos propia al desplegar; el comando no borra archivos de correo ni credenciales.

## Reportes

GET /api/admin/reports/{kind}/?file_format=csv|pdf soporta general, accesses, contents, surveys (requiere content), audit y security. Reutiliza períodos/fuentes y filtros pertinentes. Solo staff; audit además exige Superadmin. CSV es UTF-8 con BOM, encabezados y escritura por streaming, protegiendo fórmulas = + - @ y prefijos de control en campos de texto; los números conservan su tipo.

PDF utiliza ReportLab: PortalInfo UHO, título, fechas/fuente, fecha de generación, resumen, tablas con encabezados repetidos y número de página. Escapa texto; las celdas extensas se resumen y CSV conserva el contenido completo. REPORT_PDF_MAX_ROWS limita la memoria (2000 por defecto); se solicita reducir filtros o usar CSV al excederlo. El reporte de contenidos agrupa visualmente por categoría y filtra fuente DEMO/registrada y fecha de creación, no la vigencia editorial. Los contadores del dashboard siguen siendo una fotografía del CMS completo autorizado. Cada descarga queda auditada.

## Rutas y React

Además de los contratos anteriores se incorporan /api/admin/approvals/ y acciones summary/authors/decide, /api/admin/notifications/ y unread/mark_read/mark_all_read, /api/admin/access-logs/, /api/admin/security-alerts/ y scan/mark_reviewed, /api/admin/reports/{kind}/, /api/admin/estadisticas, /api/admin/logs, /api/vistas y el acceso demo. /api/docs y /api/docs/ sirven Swagger. comparison/ y open_answers/ amplían ContentViewSet sin duplicarlo.

SPA: /approvals (cola y comparación), /notifications y campana, dashboard ampliado, /statistics con Uso general/Ciberseguridad/Logs/Encuestas, /audit con filtros/detalle. Los botones CSV/PDF envían los filtros actuales y descargan archivos reales. Los enlaces de notificación vuelven a validar permisos al abrir contenido. La demo ofrece controles explícitos para registrar una visita/acceso de prueba, sin fingir autenticación institucional.

## Demostración y operación

`seed_demo --with-activity` amplía de forma opcional el seed existente; sin ese flag conserva su comportamiento anterior. Genera actividad, notificaciones, decisiones, respuestas y alertas identificadas DEMO mediante claves únicas, sin sobrescribir datos manuales, contraseñas, lectura de notificaciones ni preferencias. Los umbrales muy distintos a los predeterminados pueden cambiar las señales del ejemplo; el seed no los modifica.

La comprobación scripts/smoke_administration_http.py activa temporalmente correo local, crea su propio contenido DEMO, prueba eventos/lectura/actividad y analiza CSV/PDF de seis reportes. Después lo elimina lógicamente y restaura la preferencia solo si no cambió concurrentemente. No imprime credenciales/cookies/textos abiertos. Se conservan auditoría y archivos de correo generados por esa interacción de prueba.

Pendiente de bloques posteriores: portal pfSense y flujo real de autenticación/registro de accesos, SMTP/AGA_AUTH institucional, SIGENU/ASSET, TLS/despliegue, carga, revisión visual completa/WCAG/Manual de Identidad y caché compartida para throttling con varios workers. No se declaran verificados por compilar ni por generar datos demo.
