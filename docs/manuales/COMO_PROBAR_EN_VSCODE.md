# Cómo probar PortalInfo UHO desde VS Code

La demostración funciona en Windows, sin Docker y sin servicios institucionales. Todo queda dentro de PortalInfo-UHO. No hay que publicar nada ni conectar cuentas externas. No uses credenciales UHO reales.

## 1. Abrir la carpeta y las terminales

En VS Code, elige Archivo → Abrir carpeta y selecciona `C:\Users\Darksiders\Desktop\PortalInfo-UHO`. Abre Terminal → Nueva terminal. Comprueba que aparece esa carpeta; si estás en otra ubicación:

```powershell
cd 'C:\Users\Darksiders\Desktop\PortalInfo-UHO'
```

El botón + del panel Terminal abre otra terminal. Puedes renombrarlas Backend, Administración y Portal. No necesitas ejecutar VS Code como administrador.

## 2. Comprobar Python, Node y PostgreSQL

```powershell
python --version
node --version
.\.venv\Scripts\python.exe scripts\check_environment.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verificar_entorno.ps1
```

Este equipo utiliza Python 3.11.9, Node 24.16.0 y PostgreSQL 16 en 127.0.0.1:55432. Los scripts usan directamente .venv: no es necesario activarla. Comprueban dependencias, conexión y migraciones sin imprimir secretos. La política Bypass de esos comandos solo afecta al proceso iniciado: no cambia la política global de PowerShell.

Si falta el entorno o las dependencias, sigue INSTALACION.md. Si PostgreSQL del proyecto está detenido, ejecuta `.\scripts\start-database.cmd` y vuelve a comprobar. No lo ejecutes para reiniciar una instancia activa. No uses bootstrap_database en esta instalación existente.

## 3. Revisar .env sin sobrescribirlo

En esta entrega .env ya está configurado. Contiene SECRET_KEY y los parámetros DATABASE_* del PostgreSQL local. No copies su contenido al chat, documentos o capturas. .env.example contiene solo nombres/ejemplos; no reemplaza automáticamente .env. Para una instalación nueva sigue INSTALACION.md.

Para la demo: APP_ENV=development, PORTALINFO_DEBUG=true, AUTH_PROVIDER=demo, PORTAL_AUTH_MODE=demo, EMAIL_MODE=file. La producción rechaza demo/DEBUG y requiere una clave propia. No cambies a producción para la defensa local.

## 4. Terminal 1: iniciar Django

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_backend.ps1
```

Deja abierta esta terminal. Usa Waitress local en 127.0.0.1:8010, ocho hilos, sin instalar servicios Windows. Comprueba http://127.0.0.1:8010/api/health/; debe devolver status ok y database postgresql. Swagger: http://127.0.0.1:8010/api/docs/.

Alternativa directa si no puedes ejecutar scripts:

```powershell
.\.venv\Scripts\python.exe scripts\check_environment.py
.\.venv\Scripts\python.exe -u scripts\serve_backend.py
```

## 5. Terminal 2: iniciar React

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_frontend.ps1
```

Deja esta terminal abierta. Abre http://127.0.0.1:5174. Alternativa: `npm.cmd --prefix frontend run dev`. Usamos npm.cmd para evitar el bloqueo de npm.ps1. Los puertos 8000/5173 de otros proyectos no se modifican.

## 6. Terminal 3: comprobar y abrir el portal

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\iniciar_portal.ps1
```

Abre http://127.0.0.1:8010/portal/. El portal lo sirve Django: no hace falta iniciar un tercer servidor. Esta terminal queda libre para las pruebas. El script compila el HTML y verifica su tamaño. Alternativa: `node captive-portal/build.mjs`, después `.venv\Scripts\python.exe scripts\check_portal_size.py` y abrir la URL anterior. No abrir con file://.

## 7. Iniciar sesión y encontrar las cuentas ficticias

El archivo privado `.local/demo-credentials.txt` contiene correo y contraseña de demo.superadmin@uho.edu.cu, demo.admin@uho.edu.cu y demo.gestor@uho.edu.cu. Ábrelo únicamente en tu equipo; no lo muestres en una presentación ni lo publiques. Para visitantes, `.local/portal-demo-credentials.txt` contiene demo.estudiante, demo.trabajador y demo.institucional.

Si faltan las cuentas en una instalación nueva:

```powershell
.\.venv\Scripts\python.exe backend\manage.py seed_demo
.\.venv\Scripts\python.exe backend\manage.py seed_portal_demo
```

Ambos conservan cuentas/contraseñas ya existentes. seed_demo añade ejemplos identificados DEMO. Si activas opcionalmente `seed_demo --with-activity`, crea semilla ficticia de estadísticas separada de interacciones reales. No se requiere para iniciar.

Para probar varios roles usa perfiles o ventanas privadas independientes. Las pestañas de un mismo perfil comparten cookie y cambiar de cuenta afecta a todas. Para probar visitantes y CMS separados, utiliza también perfiles distintos si deseas independencia total.

## 8. Crear un Gestor y asignar permisos

Con Superadmin abre Usuarios → Crear registro. Usa un correo ficticio como demo.defensa@uho.edu.cu, rol Gestor, Activo y Acceso autorizado. Asigna Noticias y Encuestas. Introduce una contraseña demo nueva suficientemente larga; dejarla vacía crea una cuenta sin contraseña utilizable. Guarda.

El Gestor necesita categoría asignada y concesiones view/create/edit/delete/submit. seed_demo ya concede esas operaciones al rol Gestor para las cinco categorías base. Para una categoría nueva, ve a Permisos y crea las concesiones del usuario o rol; selecciona exactamente uno. Un Admin puede crear Gestores, pero no Administradores/Superadmins ni concesiones de rol. No edites el Superadmin protegido para probar desactivaciones: utiliza tu usuario ficticio nuevo.

## 9. Crear una noticia como Gestor

Inicia sesión con el Gestor nuevo en otro perfil. Abre Noticias → Nuevo contenido. Completa título, descripción y área. Elige vigencia: la predeterminada usa Configuración general; «Siempre» facilita una demostración sin vencimiento. Mantén visibilidad habilitada. Guarda borrador. Comprueba que aparece como Borrador y que el portal todavía no la muestra.

Abre Editar y pulsa Enviar para aprobación; también puedes usar Enviar en la tabla. Si se alcanzó el máximo visible, se avisa y se permite enviar. Un Gestor no aprueba su contenido.

## 10. Aprobar y ver la publicación

Con Admin abre la campana y Cola de aprobación. Busca la solicitud, pulsa Ver/comparar/revisar y comprueba la propuesta. Aprueba. Para probar rechazo, usa otra solicitud y escribe un motivo; no se acepta rechazo sin motivo.

En el portal pulsa Actualizar y elige Noticias. Abre tu publicación. Si no aparece, comprueba aprobación, fechas, switch, sección activa/visible y máximo visible de la categoría. El servidor mantiene las más recientes dentro del límite. No cambia el HTML por publicación nueva.

## 11. Probar una segunda revisión

Como Gestor cambia la descripción de la noticia aprobada y guarda. La revisión vuelve a Borrador; la publicación anterior sigue visible en el portal. Envía otra vez y aprueba como Admin. Pulsa Actualizar en el portal y comprueba el texto nuevo. Consulta Historial para las dos versiones. Las correcciones de Admin sobre contenido aprobado se publican directamente según la regla del sistema.

## 12. Crear y responder una encuesta

Como Gestor con Encuestas asignada, crea una encuesta interna. Añade una pregunta simple con dos opciones, una múltiple con dos opciones y una abierta si Configuración la permite. Respeta máximos y marca obligatorias. Usa vigencia Siempre, guarda y envía. Como Admin apruébala.

En el portal elige Encuestas, abre la nueva publicación y responde. Si exige autenticación, inicia sesión con un visitante ficticio. Envía y espera confirmación. El botón queda bloqueado tras éxito y Django rechaza otra participación de la misma identidad para esa versión. En errores recuperables las respuestas se conservan. Las encuestas externas abren un enlace, sin incrustar otra página.

## 13. Estadísticas, auditoría y reportes

Como Admin abre Estadísticas. Elige Hoy e Interacciones registradas para ver tus accesos/vistas/votos. La actividad del visitante demo tiene tipos demo_estudiantes/demo_trabajadores/demo_institucional. «Semilla DEMO» muestra ejemplos artificiales distintos, no tus interacciones nuevas.

En Resultados de encuestas selecciona tu encuesta. Comprueba envíos, participantes seudónimos, selecciones y textos abiertos. Descarga CSV y PDF; se usan datos reales PostgreSQL. Un porcentaje múltiple puede sumar más del 100 %. Solo Superadmin ve Auditoría y su reporte. Las alertas defensivas son indicios para revisión, no pruebas de cuenta compartida ni bloqueos automáticos.

## 14. Notificaciones y correo demo

El Admin recibe aviso al enviar; el autor recibe aprobación/rechazo/expiración registrada. La campana tiene contador propio y permite marcar lectura. Para correo, el Superadmin activa Notificaciones por correo en Configuración; EMAIL_MODE=file guarda mensajes nuevos en .local/mail sin contactar SMTP. Al terminar puedes restaurar la preferencia. Activarla no reenvía eventos históricos.

## 15. Ejecutar las comprobaciones

En la terminal 3:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\probar_sistema.ps1
# Con backend iniciado: flujo integral por HTTP, con datos propios de comprobación
.\.venv\Scripts\python.exe scripts\smoke_final_http.py
# Con backend y frontend iniciados: pruebas de navegador local
.\frontend\node_modules\.bin\playwright.cmd test --config frontend/playwright.config.js
```

El script reutiliza y conserva test_portalinfo con --keepdb; necesita CREATEDB y no elimina bases existentes. No cambian la base de trabajo. El smoke crea su Gestor/contenidos propios, prueba dos aprobaciones/encuesta/reportes y los retira al terminar: desactiva su Gestor y elimina lógicamente solo sus contenidos. Conserva historial/respuestas. No uses el identificador de otro usuario para limpiar una prueba.

## 16. Detener la demostración

Pulsa Ctrl+C en la terminal React y después en Backend. Si una terminal pide confirmación de lote, responde según el mensaje del sistema. No cierres procesos ajenos ni uses comandos de borrado. PostgreSQL puede seguir activo. Para detener únicamente el clúster local del proyecto, usa `.\scripts\stop-database.cmd` cuando no lo necesites; nunca para limpiar datos.

## 17. Errores frecuentes

| Mensaje | Qué revisar |
|---|---|
| No se permite ejecutar scripts | Usa los comandos directos o powershell.exe -ExecutionPolicy Bypass por proceso; no Set-ExecutionPolicy global |
| Falta .venv o módulos | Sigue INSTALACION.md; usa el Python de .venv |
| PostgreSQL no responde | .env, puerto 55432 y estado del clúster; no recrear la base existente |
| Puerto ocupado | Reutiliza tu servidor anterior o detenlo con Ctrl+C en su terminal; no mates otros proyectos |
| No tiene acceso | Cuenta demo registrada, autorizada/activa, contraseña y rol; no credenciales reales |
| 429 demasiados intentos | Espera el bloqueo configurado; no lo desactives para saltarlo |
| Categoría o botones ausentes | Asignación y concesiones por operación; comprueba el perfil/rol usado |
| CSRF o sesión vencida | Usa 127.0.0.1 consistentemente, recarga e inicia sesión; no desactives CSRF |
| No aparece contenido | Aprobación, versión, switch, fechas, categoría visible y máximo de publicaciones |
| Vite/esbuild Acceso denegado dentro de Codex | Restricción del sandbox al leer directorios superiores; no es un import roto. Ejecuta el script en la terminal normal de VS Code |
| Encuesta ya respondida | Una participación por identidad/navegador y versión; crea otra encuesta/version para una prueba nueva |

## 18. Qué está simulado

Las únicas identidades/concesiones de red son de demostración. La API, el CRUD, aprobaciones, votos, estadísticas, reportes y PostgreSQL son reales. No se contactan AGA_AUTH, pfSense, SMTP institucional, SIGENU ni ASSET; no se concede Internet. Los tiempos locales/carga no certifican infraestructura institucional. La publicación en GitHub/GitLab está pendiente por decisión del usuario y no se realizará.
