# Manual del Admin

Con tu cuenta ficticia entra en http://127.0.0.1:5174. Puedes administrar Gestores y sus concesiones individuales, nomencladores, contenidos, visibilidad/límites y configuración funcional. No puedes promover usuarios a Admin/Superadmin, modificar seguridad, crear/eliminar categorías ni consultar auditoría global.

En Cola de aprobación filtra solicitudes, abre la comparación y revisa la propuesta congelada. Aprobar publica esa revisión; rechazar requiere motivo. Una edición posterior invalida la solicitud anterior. Las decisiones concurrentes/reintentos no duplican publicaciones. La campana anuncia nuevos envíos y cada usuario solo ve sus propias notificaciones.

Puedes crear contenidos y enviarlos a revisión. Corregir un contenido aprobado como Admin publica una nueva versión directamente; una edición del Gestor siempre necesita reaprobación. El switch no aprueba ni modifica fechas. Eliminar contenido es lógico y conserva historial/respuestas.

En Estadísticas selecciona período/fuente, revisa gráficos y alternativa en tablas, logs, señales y resultados. Las señales se marcan revisadas sin bloquear cuentas automáticamente. Descarga CSV/PDF; los resultados/textos abiertos están restringidos a Admin/Superadmin. Los datos semilla se etiquetan y no se confunden con interacciones registradas.

Para comprobar vencimiento, consulta fechas y API; la ocultación no depende de cron. El operador ejecuta register_expirations para notificar el vencimiento una sola vez. No se ejecuta SMTP institucional desde la demo.
