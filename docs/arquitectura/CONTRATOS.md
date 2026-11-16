# Contratos REST vigentes · Entrega final local

OpenAPI 3.0.3 en /api/schema/ y Swagger local en /api/docs/. Las rutas administrativas mantienen barra final; los endpoints públicos y /auth/login, /auth/logout conservan las rutas del SRS sin barra final.

Bloque 5: el serializer de contenido acepta validity=default o su omisión al crear; calcula el rango con default_validity_days y persiste validity=custom. No cambia fechas si una edición omite vigencia. Los valores explícitos Hoy/Tres días/Semana/Mes/Siempre/Personalizado mantienen sus reglas anteriores. La configuración valida 1–3650 días. Rango estadístico que termina en año 9999 se rechaza con 400 en vez de desbordar. Login CMS/portal mantiene cuotas por IP coordinadas con PostgreSQL y Retry-After; las respuestas privadas son no-store.

Bloque 4: /portal/ sirve el HTML autónomo. GET /portal-auth/session devuelve authenticated, identity (identifier/full_name/user_type/demo/photo=null), mode, csrfToken y network_access_granted=false. POST a la misma ruta recibe username/password y crea identidad visitante sin permisos CMS; POST /portal-auth/logout invalida ese estado y la sesión anterior. CSRF obligatorio, caché no-store, 403 inválido, 429 bloqueo, 503 institucional pendiente. Identidades/IP/tipo del navegador no se aceptan como verificadas.

/api/config añade presentation.wifi_label/welcome_text públicos. /api/categorias?include_contents=false devuelve metadatos y contents=[] sin consultar publicaciones; por defecto mantiene el agregado previo. /api/{slug}, votos y vistas reutilizan contratos existentes. Los votos que exigen autenticación admiten visitante demo validado y usan HMAC estable por identidad/publicación. Guía y límites en docs/manuales/PORTAL_CAUTIVO.md.

| Grupo | Rutas y alcance |
|---|---|
| Diagnóstico | GET /api/health/; SELECT 1 en PostgreSQL, sin detalles internos |
| Sesión | GET /api/csrf/, POST /auth/login, POST /auth/logout, GET /api/me/ |
| Administración base | /api/admin/users/, roles/, permissions/, categories/, catalog-types/, catalog-items/, settings/, dashboard/, audit/ |
| CMS | /api/admin/contents/ con detalle y acciones submit/, review/, visibility/, history/, results/ |
| Metadatos de edición | GET /api/admin/content-metadata/ según categorías y operaciones autorizadas |
| API pública | GET /api/noticias, /api/eventos, /api/avisos, /api/servicios, /api/encuestas |
| Descubrimiento | GET /api/config y /api/categorias; GET /api/{slug} para categorías dinámicas |
| Respuestas | POST /api/encuestas/{id}/respuestas; CSRF obligatorio, validación y protección contra abuso |

Listas administrativas: {count,next,previous,results}, veinte resultados por página. Las listas públicas son arrays JSON limitados por categoría y no llevan contadores de registros privados. Los GET públicos solo contienen versiones aprobadas efectivamente visibles.

400 validación, 403 acceso denegado/CSRF, 404 recurso inexistente o fuera del alcance, 429 límite, 503 proveedor institucional pendiente. PATCH recomendado para cambios parciales. submit devuelve {content,warning}; review recibe {approved,reason}; visibility recibe {manual_active}.

Las cinco categorías base mantienen slugs estables para preservar los contratos públicos. Las categorías dinámicas pueden renombrar su slug, respetando unicidad y nombres reservados del sistema. Se reconocen sin generar tablas Django ni editar código de navegación.

Los contratos detallados de contenido, fechas, versiones, preguntas/opciones, resultados y política de voto están en BLOQUE_2.md. El historial refleja revisiones y aprobaciones; no es un endpoint de consulta global de auditoría.

CU-01 tiene flujo demo visitante en el portal nativo; autenticación/concesión real siguen pendientes de pfSense/AGA_AUTH. CU-02/CU-03 incluyen núcleo editorial, cola, comparación, campana y correo demo; SMTP institucional pendiente. CU-04 incluye creación/asignación/descubrimiento/API y navegación administrativa y pública dinámica local; despliegue pfSense pendiente. Reglas 10–13 y 19 se implementan en el portal del Bloque 4, con tolerancia a fallo/timeout editorial comprobada; límites móviles/rendimiento documentados. Reglas 14–17 se aplican en el CMS; regla 18 admite solo la excepción demo autorizada.

POST /api/vistas (RF-58), métricas, señales defensivas y reportes CSV/PDF están implementados en el Bloque 3. La captura ligada a autenticación institucional/pfSense continúa pendiente. Las filas semilla DEMO se distinguen y se excluyen de métricas predeterminadas.

## API del Bloque 3

| Ruta | Acceso / comportamiento |
|---|---|
| /api/admin/approvals/ | Staff: lista/detalle, summary, authors y POST {id}/decide/ con approved/reason |
| /api/admin/notifications/ | Solo destinatario: lista/detalle, unread, POST {id}/mark_read/ y mark_all_read |
| /api/admin/estadisticas | Staff: métricas calculadas por período y data_scope |
| /api/admin/logs y /api/admin/access-logs/ | Staff: logs solo lectura, paginación/filtros |
| /api/admin/security-alerts/ | Staff: lista/detalle, POST scan/ y {id}/mark_reviewed/ |
| /api/admin/reports/{kind}/ | Staff: general/accesses/contents/surveys/audit/security; audit solo Superadmin |
| /api/admin/contents/{id}/comparison/ | Categoría consultable: aprobación anterior frente a revisión actual |
| /api/admin/contents/{id}/open_answers/ | Staff: textos abiertos paginados, con período/fuente/pregunta |
| /api/vistas | POST público con CSRF, sección y contenido opcional; identidad/contexto del servidor |
| /api/demo/portal-access/ | POST con sesión demo autorizada; no concede Internet |
| /api/docs y /api/docs/ | Swagger local; producción restringida según configuración |

Los períodos today/7d/30d/month/custom se calculan en America/Havana. custom recibe date_from/date_to inclusivas; se consultan con fin exclusivo al día siguiente. data_scope=real excluye semilla; demo selecciona semilla y all mezcla explícitamente. No representa validación de personas únicas ni tráfico institucional real.

Los reportes reciben file_format=csv|pdf y los filtros del tipo correspondiente. CSV en streaming UTF-8 neutraliza fórmulas; PDF tiene límite configurable y páginas numeradas. surveys requiere content=ID. Los contratos y límites completos están en BLOQUE_3.md y OpenAPI.
