# CMS y API pública · Bloque 2

Implementación sobre el Bloque 1: se reutilizan usuarios, sesiones, roles, concesiones, nomencladores, configuración y auditoría. No se reinició PostgreSQL ni se sustituyeron migraciones. Los documentos originales conservan sus nombres completos en docs/requisitos; REQUERIMIENTOS.pdf/MOCKUP.html son los nombres alternativos del encargo, no archivos nuevos.

## Versiones y flujo editorial

Content es la revisión de trabajo; Publication conserva cada versión aprobada, con datos públicos y fechas inmutables. Content.live_publication apunta a la aprobación vigente. Crear genera borrador. Enviar registra Approval/version/submitted_at y pasa a pendiente. Admin/Superadmin aprueba o rechaza con motivo obligatorio. Un Gestor no puede revisar, incluso si es el autor.

Editar por Gestor crea una revisión de trabajo y exige nuevo envío. La publicación aprobada anterior permanece sin cambios mientras se revisa la siguiente; ni el borrador ni la revisión pendiente/rechazada se sirven públicamente. El estado editorial de la revisión puede ser pendiente mientras existe una versión pública anterior aprobada. El rechazo conserva esa versión anterior. Se documenta esta distinción para evitar confundir revisión y publicación.

Una corrección de Admin sobre contenido aprobado crea una nueva Publication directamente, conforme a RF-32. Editar una solicitud pendiente la invalida: hay que reenviar la revisión nueva. Se bloquea la fila Content durante las mutaciones para evitar aprobar una revisión obsoleta. Las operaciones editoriales y sus registros son transaccionales.

DELETE es eliminación lógica: se registra deleted_at y se retira inmediatamente de consultas administrativas normales y públicas. Permanecen versiones, solicitudes y respuestas. No se eliminan preguntas respondidas ni tablas históricas. El historial accesible por categoría muestra publicaciones y solicitudes; la auditoría global continúa reservada al Superadmin.

Cambiar categoría exige permisos en la categoría de origen y destino. Solo se permiten traslados entre categorías del mismo tipo; no se transforma una encuesta en evento con datos incompatibles. Una categoría dinámica usa tipo generic, campos comunes y extra_fields de texto; required_fields configura campos obligatorios. No se generan tablas/endpoints de código nuevos por categoría. El tipo estable de las cinco categorías base se migró desde sus slugs originales.

## Visibilidad y vigencia

queries.visible_publications centraliza todas las consultas. Solo selecciona la versión que coincide con live_publication, no eliminada, con switch manual activo, categoría activa y sección visible, inicio alcanzado y fin no alcanzado. Un ranking SQL por categoría aplica max_visible. Se ordena por starts_at descendente y, en empate, content_id descendente. El ranking se aplica en una subconsulta antes de filtrar un identificador; así el endpoint de respuestas tampoco acepta una encuesta excluida por el límite.

El switch modifica manual_active; no crea aprobaciones ni extiende fechas. La visibilidad temporal usa las fechas de la versión aprobada, no fechas cambiadas en un borrador. El estado public_visible del listado considera también el límite, no solo elegibilidad.

| Modalidad | Cálculo backend, America/Havana |
|---|---|
| Hoy | Desde ahora hasta la próxima medianoche local, fin exclusivo |
| Tres días | Desde ahora durante 72 horas |
| Esta semana | Desde ahora hasta el lunes siguiente a las 00:00 locales |
| Este mes | Desde ahora hasta el primer día del mes siguiente a las 00:00 locales |
| Siempre | Desde ahora, sin fecha final |
| Personalizado | Dos fechas conscientes de zona; fin estrictamente posterior al inicio, exclusivo |

El formulario datetime-local utiliza la zona del navegador y envía fechas ISO con offset/UTC. La presentación de fechas usa America/Havana. Una edición sin cambios de vigencia conserva las fechas; cambiar de modalidad recalcula en backend.

El contenido vencido desaparece por consulta, sin depender de cron. `python backend/manage.py register_expirations` bloquea y marca una sola vez cada publicación vencida, registra auditoría y una notificación persistente para su autor. Su programación y la campana/envío SMTP pertenecen al Bloque 3.

Superar max_visible produce advertencia al enviar, sin rechazar la solicitud. La API mantiene siempre el máximo. Límites de texto, preguntas/opciones y campos dinámicos se validan en backend; React consulta los mismos límites. Los límites de caracteres se aplican al guardar/enviar/aprobar, sin truncar silenciosamente datos existentes.

## Encuestas y respuestas

Survey especializa Content. Question tiene kind, required, position y archived; Option pertenece a Question. Editar una definición archiva preguntas y crea las nuevas en la misma transacción. Las definiciones previas permanecen y Publication guarda sus identificadores/textos/opciones. Una versión pública mantiene preguntas estables aunque haya ediciones pendientes.

Submission identifica una participación en una Publication; Response referencia Submission y Question, con texto y opciones M2M. Hay restricciones únicas publicación/identidad y participación/pregunta. Las relaciones existentes se preservaron con submission nullable para respuestas anteriores al módulo. Si hubiese respuestas históricas cargadas manualmente sin Submission, se conservan en la base y requieren conciliación antes de agregarlas a una versión; no se atribuye una versión inventada.

El POST exige encuesta interna efectivamente pública, preguntas de su definición, opciones propias, unicidad, cardinalidad simple/múltiple, campos obligatorios y límites. Rechaza respuestas para borradores, futuros, vencidos, secciones ocultas y encuestas excluidas por el máximo. Una encuesta externa requiere enlace http(s) y no contiene preguntas internas.

Se exige CSRF también a visitantes anónimos. El visitante obtiene token/cookie en GET /api/csrf/. Las sesiones autenticadas usan una clave HMAC de la identidad; los anónimos, un identificador aleatorio en cookie firmada HttpOnly, SameSite=Lax, Secure en producción, con duración de 90 días. Se admite una participación por identidad/navegador y versión publicada. Una nueva versión permite volver a votar; los resultados se separan por versión. No se considera la IP una identidad personal.

Limitaciones: eliminar cookies o cambiar navegador permite otra participación anónima; una primera petición simultánea desde un navegador sin cookie aún puede obtener identificadores distintos. La restricción PostgreSQL protege identidades ya establecidas. Hay límite de 10 intentos por minuto/IP, que puede afectar usuarios detrás de NAT; no se aceptan cabeceras X-Forwarded-For arbitrarias como identidad. El caché de throttling de desarrollo es local: varios workers requieren caché compartida antes de producción.

Si vote_requires_auth está habilitado se requiere sesión local autorizada. La demo no proporciona autenticación institucional a visitantes; esa integración permanece pendiente. Los porcentajes usan respuestas efectivas por pregunta; una pregunta múltiple puede sumar más del 100 %. Los textos abiertos y resultados completos solo se consultan por Admin/Superadmin. Nunca salen en GET públicos.

## API y pantallas

| Ruta | Comportamiento |
|---|---|
| /api/admin/contents/ | GET paginado, POST; detalle GET/PUT/PATCH/DELETE |
| /api/admin/contents/{id}/submit/ | POST de envío; devuelve content y warning |
| /api/admin/contents/{id}/review/ | POST {approved, reason}; revisión solo staff |
| /api/admin/contents/{id}/visibility/ | POST {manual_active}; requiere edit |
| /api/admin/contents/{id}/history/ | GET versiones/solicitudes según categoría |
| /api/admin/contents/{id}/results/ | GET resultados por versión; solo staff |
| /api/admin/content-metadata/ | GET categorías autorizadas/operaciones, áreas/tipos y límites de encuesta, sin parámetros de seguridad |
| /api/noticias, eventos, avisos, servicios, encuestas | GET de publicaciones visibles, listas JSON |
| /api/{slug} | GET para cualquier categoría, incluidas dinámicas; slug inexistente 404 |
| /api/categorias | GET secciones habilitadas con sus contenidos visibles |
| /api/config | GET configuración pública de secciones/límites y preferencias de encuesta |
| /api/encuestas/{id}/respuestas | POST {answers:[{question, options:[], value}]} |

Filtros administrativos: category, category__content_type, state, manual_active, area, date_from/date_to (visibilidad), event_from/event_to (fecha del evento), visibility=active/hidden/expired/future. search consulta título/descripción; ordering admite fechas, título y event__event_at. Veinte resultados por página. active refleja la versión pública; expired/future filtran las fechas de la revisión de trabajo. hidden significa cualquier contenido no visible, incluidos borradores, vencidos o fuera del máximo.

La SPA descubre categorías desde metadatos sin cambios de código. Rutas /content/{slug}, /contents, /contents/pending, /contents/active y /contents/hidden. Hay filtros, formularios específicos, detalle/vista previa, historial, switches, confirmación de eliminación, cola de aprobación y resultados con barras meter. SurveyEditor añade/elimina/reordena preguntas y opciones, cambia tipos y obligatoriedad. Se conservan datos al fallar guardado y se bloquea el doble envío. Los diálogos tienen foco, retorno de foco, Escape y ciclo Tab; el texto se renderiza con escape React, sin dangerouslySetInnerHTML.

El detalle/vista previa refleja la revisión de trabajo y advierte cuando existe una versión aprobada; no afirma que los cambios pendientes ya estén publicados. Los enlaces solo admiten http/https sin credenciales y no se comprueba conectividad de sitios institucionales.

Datos demo: seed_demo invoca seed_content_demo. Crea 42 ejemplos identificados DEMO (seis categorías por siete escenarios: borrador, pendiente, aprobado, rechazado, oculto, vencido y futuro). seed_key evita duplicados incluso tras eliminación lógica. No sobrescribe filas existentes ni genera participaciones simuladas. La comprobación HTTP sí crea una respuesta de prueba real en una encuesta de comprobación luego eliminada lógicamente.
