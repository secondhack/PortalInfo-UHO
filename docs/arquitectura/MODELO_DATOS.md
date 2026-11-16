# Modelo de datos vigente

PK bigint autogenerada, salvo GlobalSettings (singleton 1) y especializaciones de contenido OneToOne con PK/FK. Fechas conscientes de zona, presentación America/Havana.

| Entidad | Relaciones y restricciones |
|---|---|
| Role | Código único superadmin/admin/gestor; nombre editable; capacidades administrativas fijas como frontera de seguridad. |
| User | AbstractUser, correo único @uho.edu.cu, Role PROTECT, categorías M2M, autorización previa, demo/protegido, uid AGA opcional único. Hash solo demo; sin perfiles inventados. |
| Grant | Usuario o rol mediante CHECK XOR, categoría y operación. Unicidad por sujeto/categoría/operación; CASCADE al retirar sujeto/categoría. |
| CatalogType / CatalogItem | Nombre/slug de tipo únicos; ítem único por tipo/nombre. Tipo y padre PROTECT, validación de ciclos. Áreas/departamentos/cargos/carreras/tipos de servicio configurables. |
| Category | Nombre/slug únicos; activa/visible/dinámica; límites positivos y required_fields JSON. content_type estable news/event/notice/service/survey/generic. PROTECT si hay contenido/versiones. |
| Content | Categoría/autor PROTECT; texto, estado de revisión, vigencia, fechas, switch y campos extra. revision, submitted_at, deleted_at, seed_key único nullable y live_publication SET_NULL. Índice categoría/estado/fechas y CHECK fin > inicio. |
| News / Event / Service | OneToOne Content CASCADE; área PROTECT. News: enlace opcional. Event: fecha independiente de visibilidad, contacto y convocatoria. Service: URL requerida y tipo opcional PROTECT. |
| Aviso / categoría genérica | Solo Content; no tablas vacías ni tablas nuevas por categoría dinámica. |
| Publication | Content/Category PROTECT, versión única por contenido, snapshot público JSON y fechas, aprobador PROTECT y marca de expiración. Aprobador nullable únicamente para preservar aprobaciones históricas sin revisor conocido; nuevas revisiones siempre registran actor. Índice categoría/fechas. |
| Survey / Question / Option | Survey OneToOne; externa mediante URL, interna mediante preguntas. Question: tipo, texto, required, archived y orden único entre preguntas activas. Option pertenece a Question. Editar archiva definiciones anteriores y crea nuevas atómicamente. |
| Submission / Response | Participación FK Publication PROTECT, identidad seudónima y fecha; única por publicación/identidad. Response protege pregunta y participación, almacena texto/opciones M2M, única por participación/pregunta. submission nullable conserva filas históricas sin atribuir versiones inventadas. |
| Approval | Content/solicitante/revisor PROTECT, version de revisión, estado, motivo y fechas. Editar invalida solicitudes pendientes anteriores. |
| Notification | Destinatario CASCADE, tipo, mensaje, lectura y fecha. event_key único por destinatario, título/referencia, read_at y DEMO; eventos editoriales y campana operativos. |
| GlobalSettings | Singleton CHECK id=1, límites, bloqueo, duración de sesión, retención y preferencias sin secretos. |
| AuditEvent | Actor SET_NULL, acción/entidad/fecha indexadas, recurso, IP, User-Agent limitado y metadatos seleccionados. API solo lectura del Superadmin. |
| AccessLog / ContentView | Identidad/sección/contenido, IP, dispositivo y fecha; contenido SET_NULL. Captura pública de vistas y acceso demo implementados; identidad institucional real pendiente. |

La revisión de trabajo y la publicación aprobada se separan. queries.visible_publications aplica versión vigente, eliminación lógica, switch, categoría/sección habilitada, rango temporal y máximo por categoría. Expirar no cambia silenciosamente el estado editorial. El proceso register_expirations genera eventos sin ser necesario para ocultar.

El Bloque 2 implementa validaciones intermodelo, límites de encuestas/campos y transacciones editoriales. Las respuestas referencian definiciones preservadas; los resultados se separan por versión. Detalles y limitaciones en BLOQUE_2.md.

Cinco migraciones incrementales: catalogs.0002/0003, content.0002/0003 y approvals.0002. Backfill compatible de tipos base y contenido previamente aprobado. Se conservan las ocho 0001 del proyecto y las quince migraciones Django. No ejecutar resets, flush ni borrar migraciones sobre datos existentes.

## Cambios incrementales del Bloque 3

- Approval.proposal: JSON inmutable de la solicitud; backfill solo de revisiones reconstruibles. La concurrencia utiliza la fila Content ya existente y no añade estados redundantes.
- Notification: title, resource_type/resource_id, event_key, read_at y demo; unicidad destinatario/evento e índice destinatario/lectura/fecha. MailDelivery OneToOne CASCADE con estado, intentos, error seguro y fecha de entrega.
- AccessLog: event_type (access/view), device clasificado, demo y seed_key único nullable; índices identidad/fecha y evento/fecha. ContentView enlaza AccessLog OneToOne SET_NULL, Category SET_NULL y añade identidad/tipo/demo/seed_key.
- SecurityAlert: identidad seudónima, tipo/prioridad, ventana, evidencia JSON, clave única, revisión/actor SET_NULL y DEMO. Índices de prioridad/revisión/fecha. No almacena prueba concluyente ni ejecuta bloqueos.
- Submission añade demo y seed_key único para separar ejemplos de interacciones. Los resultados cuentan participaciones y respuestas por versión sin exponer claves personales.
- AuditEvent añade entity indexada; backfill de entidades derivadas de acciones existentes. GlobalSettings añade ventana y umbrales de reglas defensivas con validadores.

Ocho migraciones nuevas: content.0004, analytics.0002, approvals.0003/0004, audit.0002/0003, notifications.0002 y settings_app.0002. Total actual: 36 migraciones aplicadas (28 anteriores preservadas). Política de eliminación restringida a logs por mantenimiento autorizado; contenidos/versiones/respuestas permanecen intactos.

## Integración del portal · Bloque 4

No añade tablas/migraciones. La sesión Django almacena portal_visitor: identificador ficticio, vencimiento y sello HMAC del hash para revocación. Las cuentas ficticias separadas se guardan con hashes en .local/portal-demo-users.json, sin crear User/Role y sin persistir contraseñas introducidas ni datos institucionales. Las credenciales generadas se entregan en archivo privado excluido del repositorio.

Bloque 5 conserva las 36 migraciones. validity=default es únicamente entrada de serializer: se persiste como custom con inicio y fin calculados desde default_validity_days (1–3650). Editar sin cambiar vigencia preserva esas fechas. No se cambia el esquema ni se reescriben registros existentes. Los locks de login son asesores/transaccionales PostgreSQL y no necesitan tablas nuevas. La base test_portalinfo queda separada/conservada con --keepdb; el respaldo no sobrescribe la base de trabajo.

AuditEvent reutiliza acciones portal_auth.*; AccessLog/ContentView conservan contexto y HMAC de visitante con tipos demo_estudiantes/demo_trabajadores/demo_institucional. demo=True sigue marcando semilla artificial del Bloque 3; interacciones reales del simulador son demo=False con esos tipos explícitos. Submission.respondent_key usa HMAC de visitante con unicidad publicación/identidad existente. No se alteran definiciones/versiones anteriores ni se reasignan participaciones históricas.
