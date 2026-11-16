# Permisos y fronteras de confianza

| Operación | Superadmin | Admin | Gestor |
|---|---|---|---|
| Usuarios | Crear/consultar/editar; Superadmin protegido | Solo Gestores | Sin acceso |
| Roles | Consultar/renombrar | Consultar | Sin acceso |
| Concesiones | Usuarios y roles | Solo usuarios Gestores | Sin administración |
| Crear/eliminar categoría | Sí | No | No |
| Visibilidad/límites/nomencladores | Sí | Sí | No |
| Configuración funcional | Sí | Sí | No |
| Seguridad/auditoría global | Sí; auditoría solo lectura | No | No |
| Contenido | Todas las categorías | Todas las categorías | Categoría asignada y concesión por operación |
| Aprobar/rechazar | Sí | Sí | No, tampoco sus propios contenidos |
| Resultados/textos abiertos | Sí | Sí | No |

Las capacidades reservadas son fronteras fijas de los tres roles exigidos. Las concesiones de contenido son configurables por usuario/rol/categoría/operación (view/create/edit/delete/submit), aditivas. Quitar la categoría impide operar aunque subsista una concesión de rol. Para consultar/navegar se requiere view; al escribir se comprueba además la operación concreta. Trasladar exige permisos en origen y destino y tipos compatibles.

category_allowed y queries.allowed_categories centralizan autorización. Las búsquedas de objetos se restringen por categoría antes de editar. React adapta botones; el backend aplica las restricciones obligatorias. Autor, revisión y estado no se aceptan como campos arbitrarios para saltarse el flujo editorial. Un switch no aprueba ni renueva fechas.

Una revisión pendiente no sustituye la versión pública aprobada. Admin puede corregir directamente contenido aprobado; Gestor requiere nueva aprobación. Eliminar es lógico, preservando respuestas/historial. Historial editorial se limita a categorías consultables; auditoría global permanece reservada al Superadmin.

Los serializers no exponen contraseñas, grupos, is_superuser ni permisos Django. Admin no puede ascenderse, promover Gestores, editar Superadmins, delegar permisos de rol ni cambiar seguridad. protected no es editable. Sesiones desactivadas pierden autenticación y retirar authorized bloquea las APIs protegidas. Logout invalida el estado del servidor, incluida la cookie anterior.

GET públicos no exponen autor/aprobador, claves de voto, respuestas, auditoría ni seguridad. Votos requieren CSRF, incluso anónimos; validación contra la definición aprobada, deduplicación transaccional y throttle por REMOTE_ADDR. NUM_PROXIES=0 evita confiar en cabeceras IP arbitrarias. No se considera la IP un identificador personal. Política y límites del voto en BLOQUE_2.md.

## Permisos administrativos del Bloque 3

| Operación | Superadmin | Admin | Gestor |
|---|---|---|---|
| Notificaciones | Solo propias | Solo propias | Solo propias |
| Cola y decisiones | Sí | Sí | No; consulta sus contenidos y estados |
| Dashboard | Global | Global | Categorías autorizadas, sin accesos globales |
| Estadísticas/logs/alertas | Sí | Sí | No |
| Revisar señal defensiva | Sí, auditado | Sí, auditado | No |
| CSV/PDF generales y encuestas | Sí | Sí | No |
| CSV/PDF de auditoría | Sí | No | No |
| Reglas de seguridad/correo | Configurar | No | No |
| Aplicar retención | Operador de shell autorizado, con confirmaciones | No | No |

Los endpoints de notificaciones filtran destinatario antes de buscar el identificador. Las acciones de lectura no permiten cambiar mensaje, destinatario o referencia ni eliminar filas. Las decisiones verifican solicitud/revisión y bloquean Content; no se aplican por modificar libremente state.

/api/vistas rechaza identidades enviadas por JSON, valida visibilidad y deriva contexto de proxies explícitamente confiables. Las identidades almacenadas son seudónimas; las anónimas no se tratan como cuentas reales. El acceso demo usa la sesión local y no concede Internet. Toda exportación comprueba permiso antes de consultar/generar datos; los textos abiertos solo se incluyen para staff autorizado.

No existe eliminación de logs por API. maintain_logs simula por defecto; aplicar exige acceso al sistema operativo y --apply/--authorized-by/--confirm-days. El identificador Superadmin deja trazabilidad, no sustituye autenticación del operador en el sistema operativo.

## Visitantes del portal · Bloque 4

/portal/ y GET /portal-auth/session son públicos. POST sesión/logout, vistas y votos requieren CSRF incluso sin CMS. Un visitante demo solo adquiere identidad para sesión y encuestas: ninguna capacidad administrativa. Login CMS no crea identidad visitante. Logout del portal rota/invalida la cookie anterior, conserva una identidad CMS separada si existe y no modifica la red.

Tipos/identificadores proceden del proveedor del servidor. Intentos y bloqueo por IP configurables, serializados mediante bloqueo asesor PostgreSQL. La IP procede de client_context/proxies autorizados. Demo se rechaza en producción; institucional responde 503 sin contrato. El portal no recibe respuestas ajenas, resultados reservados, auditoría, hashes ni secretos. Orígenes adicionales requieren PORTAL_ALLOWED_ORIGINS explícito y estrategia compatible de cookies/TLS/CSP.

Cierre final: login CMS también serializa intentos concurrentes por IP y devuelve Retry-After al bloquear. El tamaño de credenciales de entrada está acotado; los hashes ficticios desconocidos usan padding compartido sin crear usuarios. Respuestas administrativas/de sesión usan Cache-Control no-store. La configuración de producción rechaza demo/DEBUG y claves placeholder/cortas. No se usa CORS comodín. Estas defensas y las pruebas locales no equivalen a auditoría externa ni a despliegue TLS certificado.
