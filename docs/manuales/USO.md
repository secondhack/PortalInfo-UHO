# Uso local

## Portal cautivo · Bloque 4

Con Django iniciado, abrir http://127.0.0.1:8010/portal/. El acceso visitante usa las cuentas ficticias de .local/portal-demo-credentials.txt, separadas de las del CMS. Si faltan, ejecutar `.venv\Scripts\python.exe backend\manage.py seed_portal_demo`. La sesión no modifica Internet ni concede permisos administrativos.

El formulario aparece antes de cargar contenidos. Elegir sección para consultar publicaciones aprobadas; «Ver información» amplía texto/enlaces y registra la primera apertura. «Actualizar» consulta configuración, descubre categorías nuevas y retira las deshabilitadas. El login sigue operativo si falla solo la API editorial.

En Encuestas, abrir una publicación, completar preguntas y enviar. El servidor valida estado/opciones/obligatorios; el botón evita doble envío y los fallos conservan respuestas. Algunas requieren iniciar sesión. Las externas abren otra ventana y pueden necesitar red institucional. Cerrar sesión invalida visitante y cookie anterior.

Estadísticas del CMS refleja estas interacciones con tipos demo_estudiantes/demo_trabajadores/demo_institucional. No son autenticaciones institucionales ni semilla artificial: la fuente «Interacciones registradas» las incluye. Guía, privacidad y límites en PORTAL_CAUTIVO.md. La medición de 200 conexiones detectó rechazos en runserver; no acredita despliegue institucional ni compatibilidad visual móvil.

## Panel administrativo

Inicie los servicios siguiendo README. Abra http://127.0.0.1:5174. Las cuentas ficticias y contraseñas generadas se encuentran en .local/demo-credentials.txt; no compartir ese archivo ni usar credenciales reales.

Superadmin puede registrar usuarios por correo institucional, elegir rol y asignar categorías. La contraseña demo es opcional al registrar; sin ella la cuenta no puede iniciar sesión local hasta asignarle una. La cuenta Superadmin no puede desactivarse, degradarse ni eliminarse. Admin administra únicamente Gestores.

En Usuarios, buscar por correo y filtrar por estado; Editar permite modificar rol dentro del alcance, categorías y autorización. Desactivar impide acceso. Las tablas están paginadas. Las categorías se seleccionan con Ctrl/selección múltiple en escritorio o el selector nativo móvil.

En Permisos, seleccionar un usuario **o** un rol, una categoría y una operación. Los permisos del Gestor requieren además categoría asignada en Usuarios. Los permisos heredados del rol aparecen como registros separados.

Categorías permite crear secciones dinámicas (Superadmin), definir límites y ocultar/mostrar secciones (Admin/Superadmin). Nomencladores mantiene valores de tipos configurables y dependencias jerárquicas; se recomienda desactivar elementos en uso. La integridad referencial impide eliminarlos si tienen referencias.

Configuración guarda preferencias persistentes. Los campos de seguridad solo son accesibles al Superadmin. Cambios de duración se aplican al autenticar o renovar consulta de sesión. Retención se registra como política, todavía sin proceso de eliminación automática.

Auditoría es solo consulta para Superadmin. No guarda contraseñas ni cuerpos de solicitudes. Próximos módulos identifica funcionalidades pendientes. Salir invalida la sesión en el servidor.

## Gestión de contenidos · Bloque 2

Desde la barra lateral se descubren las categorías permitidas. El Gestor demo inicial tiene Noticias y Eventos; para probar Encuestas u otra categoría, Admin/Superadmin debe asignársela y conceder sus operaciones en Usuarios/Permisos.

En cada listado: buscar, filtrar estado/área/fechas/visibilidad efectiva, ordenar y paginar. Elegir si las fechas filtran vigencia o inicio del evento. El switch controla la visibilidad manual, sin saltarse aprobación ni fechas. «En portal» indica visibilidad efectiva incluyendo el máximo por categoría.

Nuevo contenido/Editar abre el formulario correspondiente: área y enlace para noticias; fecha/contacto/convocatoria para eventos; enlace obligatorio para servicios; título y descripción para avisos/categorías genéricas. Los campos requeridos dinámicos proceden de la categoría. Los contadores reflejan sus límites actuales.

Encuestas permite elegir interna o enlace externo. En interna: añadir preguntas simples, múltiples o abiertas, marcar obligatoriedad, añadir/eliminar opciones y subir/bajar preguntas. Los botones respetan los límites configurados. Vista previa muestra la revisión sin registrar votos. Resultados solo está disponible para Admin/Superadmin y separa versiones; las respuestas abiertas no son públicas.

Guardar borrador no publica. Enviar para aprobación registra una solicitud; si se alcanzó el máximo visible, se advierte pero se permite continuar. La cola Pendientes permite aprobar o rechazar con motivo. Una modificación del Gestor necesita nueva aprobación y mantiene intacta la versión pública anterior; una corrección de Admin sobre contenido aprobado se publica directamente.

Eliminar pide confirmación y hace eliminación lógica, conservando solicitudes, publicaciones y respuestas. Historial muestra versiones y revisiones según acceso por categoría. Para editar una encuesta ya respondida se conserva la definición previa y sus resultados; una nueva versión permite una participación nueva por identidad/navegador.

Vigencia: Hoy, Tres días, Esta semana, Este mes, Siempre o Rango personalizado. Los períodos se calculan en America/Havana; los campos de fecha usan la zona del navegador y envían fechas con zona. Expiración retira contenidos de la API incluso sin ejecutar tareas de mantenimiento.

Los datos semilla están identificados DEMO. seed_demo puede repetirse sin sobrescribir cuentas ni contenidos manuales. La herramienta smoke_content_http crea comprobaciones propias, incluye un voto de prueba real y elimina lógicamente sus contenidos al terminar.

## Operación del Bloque 3

La cola «Cola de aprobación» está disponible para Admin/Superadmin. Filtrar por categoría, autor, fecha, título y estado; abrir una solicitud para comparar las dos versiones. Aprobar registra al responsable y notifica al autor; rechazar requiere un motivo. El historial conserva la propuesta original aunque el contenido vuelva a editarse.

La campana muestra mensajes propios y contador real, actualizado cada 30 segundos en pestañas visibles. Abrir el panel, marcar uno o todos, o ir a «Notificaciones» para paginar. Los enlaces abren el contenido aplicando permisos actuales. El Gestor no puede consultar mensajes ajenos.

Para correo demo, Superadmin activa el parámetro de notificaciones por correo en Configuración y genera un evento nuevo. Los mensajes se guardan en .local/mail; no se usa un servidor institucional. Las notificaciones antiguas no se reenvían al activar el parámetro. El estado de salida aparece en el inbox y los fallos se reintentan con deliver_notifications.

Dashboard y Estadísticas permiten período y fuente de actividad. «Interacciones registradas» excluye semilla; «Semilla DEMO» permite presentar ejemplos ficticios explícitos. Los totales de contenido describen el CMS actual y avisan si incluyen ejemplos. Los reportes de contenidos sí aplican fecha de creación y fuente elegidas.

En Estadísticas: Uso general ofrece gráficos/tablas y botones de reporte; Ciberseguridad analiza las reglas configuradas, muestra evidencia y permite marcar revisada una señal sin bloquear cuentas; Logs permite filtros/detalle; Encuestas distingue envíos/identidades/respuestas y pagina textos abiertos autorizados. Las señales no prueban uso compartido ni identifican físicamente un equipo.

Los controles de «Comprobar registro de actividad» generan una interacción real de prueba con la sesión demo; no autentican en WiFi. El portal definitivo aún debe conectarse al flujo institucional.

Auditoría, solo Superadmin, filtra actor/acción/entidad/período, muestra resúmenes y permite exportar CSV/PDF. No hay botones para alterar o borrar eventos. Las exportaciones conservan filtros y no incluyen secretos.

Mantenimiento: register_expirations registra vencimientos una sola vez; scan_security ejecuta reglas; deliver_notifications reintenta pendientes; maintain_logs simula la retención sin borrar. Aplicar retención exige operador autorizado y flags explícitos de política, únicamente por consola. No ejecutar --apply como una comprobación rutinaria.
