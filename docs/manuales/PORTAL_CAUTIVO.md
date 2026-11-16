# Portal cautivo institucional · Guía local · revisión final

## Ejecución local

Desde C:\Users\Darksiders\Desktop\PortalInfo-UHO:

```powershell
# Solo si PostgreSQL del proyecto está detenido; no reiniciar una instancia activa
.\scripts\start-database.cmd
# Semilla idempotente, no modifica cuentas CMS
.\.venv\Scripts\python.exe backend\manage.py seed_portal_demo
node captive-portal/build.mjs
.\.venv\Scripts\python.exe scripts\check_portal_size.py
# Terminal 1
.\scripts\start-backend.cmd
# Terminal 2, administración opcional
.\scripts\start-frontend.cmd
```

Portal: http://127.0.0.1:8010/portal/. Panel: http://127.0.0.1:5174. API/Swagger en 8010. Se conservan 8000/5173 y PostgreSQL 5432 de otras aplicaciones. No usar file://: las sesiones y los votos necesitan HTTP/cookies/CSRF.

Las cuentas demo.estudiante, demo.trabajador y demo.institucional tienen contraseñas aleatorias en .local/portal-demo-credentials.txt. Son identidades ficticias; no usar credenciales UHO reales. No aparecen en User ni tienen rol/permisos CMS. Las cuentas administrativas y sus credenciales permanecen intactas.

## Arquitectura y artefacto

Django proporciona API, sesiones y /portal/. React administra contenidos/estadísticas en otro frontend. captive-portal/src/index.html contiene HTML semántico estático; src/portal.css, estilos; src/portal.js, lógica nativa. build.mjs usa el esbuild existente en frontend/node_modules para minificar CSS/JS e incluirlos inline en dist/index.html. No se introduce dependencia de ejecución en React/Vite.

El CSS es un subconjunto propio compatible con clases Bootstrap 5: container, card, btn, form-control, form-label, nav y utilidades necesarias. No se incluye Bootstrap completo ni su JavaScript. Sin CDN, fuentes externas, imágenes, videos, documentos o gráficos. La marca UHO es texto, siguiendo la referencia azul #003366/naranja #FF6F00 del mockup original; no se inventa un logo oficial ni se acredita el Manual de Identidad, que no está disponible.

El HTML final mide **24539 bytes sin gzip**, frente al límite de 204800. El build y scripts/check_portal_size.py fallan si se supera. .gitignore permite conservar específicamente ese artefacto. Docker Compose monta dist/ de solo lectura; Docker no se ha ejecutado aquí.

El diseño empieza en una columna para móvil, pasa a tarjetas en dos columnas desde 600 px y divide acceso/información desde 980 px. Usa minmax(0,1fr), ajuste de palabras y controles de al menos 44 px. Hay etiquetas, fieldsets/legends, skip-link, foco visible, aria-live, aria-expanded/aria-busy y movimiento reducido. Las pruebas estructurales no certifican geometría en 360–480 px ni WCAG AA: revisar en navegadores reales.

## Contratos consumidos

| Método y ruta | Uso |
|---|---|
| GET /portal-auth/session | Estado, modo, identidad pública y token CSRF; no-store |
| POST /portal-auth/session | username/password ficticios, validación servidor y registro de acceso |
| POST /portal-auth/logout | Invalida visitante y cookie anterior por rotación de sesión |
| GET /api/config | Secciones habilitadas, límites de encuestas y presentation público |
| GET /api/categorias?include_contents=false | Descubrimiento ligero; sin parámetro conserva contents del contrato anterior |
| GET /api/{slug} | Publicaciones aprobadas y visibles, cinco tipos base y categorías nuevas |
| POST /api/encuestas/{id}/respuestas | answers con question/options/value de la versión aprobada |
| POST /api/vistas | section y content opcional; no acepta identidad del navegador |

Cada sección se carga bajo demanda, sin descargar todo el agregado para descubrir categorías. Se conserva el orden backend. El portal no reproduce permisos ni filtra vigencia: muestra publicaciones devueltas por la consulta central. «Actualizar» recarga configuración/categorías/sección; al desaparecer una sección, elimina su navegación/contenido. Una categoría nueva aparece sin modificar HTML. Configuración y descubrimiento no condicionan el login.

Noticias: título/resumen/área/fecha y texto ampliado. Eventos: inicio/contacto/convocatoria. Avisos: texto/fecha. Servicios: enlace seguro y aviso de posible restricción a red institucional. Los campos escalares genéricos se muestran como texto. No se comprueba disponibilidad de sitios externos ni se incrustan páginas.

Encuestas internas: definición real de Publication, simple/múltiple/abierta, hasta 4000 caracteres, obligatorias y límites. Django vuelve a comprobar estado/versión/opciones/permisos/duplicación. El botón se bloquea durante envío y tras éxito; un fallo conserva respuestas. Las externas abren http(s) con noopener/noreferrer, sin iframe. vote_requires_auth admite visitante demo validado o sesión CMS autorizada; el visitante tiene precedencia en estadísticas/votos. No se inventan resultados.

## Autenticación y fallo independiente

PORTAL_AUTH_MODE=demo solo se permite fuera de producción. DemoVisitorProvider valida hashes Django de cuentas ficticias en .local/portal-demo-users.json. seed_portal_demo no sobrescribe ese archivo ni regenera contraseñas existentes. Los nombres no proceden de AGA_AUTH; foto pública null y avatar textual.

La identidad ocupa portal_visitor en la sesión Django, sin ejecutar el login administrativo ni otorgar permisos CMS. Se rota la clave al entrar/salir; logout elimina la sesión anterior y conserva una identidad CMS separada si existe. GlobalSettings.session_seconds fija duración, comprobada en servidor y renovada. Desactivar la cuenta o cambiar el hash invalida su estado anterior. Cookies HttpOnly/SameSite=Lax y Secure en producción; sin tokens/contraseñas en localStorage/sessionStorage. El campo contraseña se borra al enviar y no se registra.

Los fallos se cuentan por IP/ventana mediante login_attempts/lockout_seconds, separados del CMS. Un bloqueo asesor transaccional PostgreSQL por IP serializa intentos entre workers. Tras el umbral: 429 y Retry-After. AuditEvent guarda portal_auth.failed/blocked/login/logout sin contraseña ni usuario introducido. Un acceso exitoso genera AccessLog con HMAC de identidad, tipo demo_estudiantes/demo_trabajadores/demo_institucional, IP y navegador validados en servidor. Las interacciones reales de la demo conservan demo=False: demo=True sigue reservado a semilla ficticia del Bloque 3. El prefijo del tipo evita confundirlas con accesos institucionales.

El formulario existe antes de JavaScript. Las peticiones /portal-auth/ son independientes de configuración/descubrimiento/contenidos. Timeout 8 segundos; fetch + AbortController cuando existen, XHR con timeout/cookies como alternativa sin Promise/fetch/AbortController. Los fallos editoriales muestran «No se pudo cargar la información institucional en este momento.» y permiten reintentar, sin ocultar/deshabilitar el formulario. Si falla autenticación se informa por separado. Una caída completa de Django/PostgreSQL también afecta al proveedor local: no se promete aislamiento de infraestructura inexistente.

La demo avisa «Entorno de demostración: el acceso a Internet no se modifica.». network_access_granted es false. Sin interceptación, reglas de firewall, configuración de red o contactos institucionales.

## Modo institucional y despliegue estático futuro

PORTAL_AUTH_MODE=institutional usa InstitutionalVisitorProvider, que responde 503 hasta recibir contrato autorizado. Su interfaz recibe username/password y deberá devolver identificador/nombre/tipo verificados en servidor, sin persistir credenciales/fotos. Conceder/revocar red pertenece a un adaptador pfSense independiente. No se suponen URLs, tokens o parámetros pfSense. VerifiedPortalIdentity del Bloque 3 queda disponible para el contrato real.

Para dist/index.html fuera de Django, preferir proxy de mismo origen para /portal-auth/ y /api/. Se pueden fijar PORTAL_API_BASE y PORTAL_AUTH_BASE al ejecutar build.mjs: acepta orígenes HTTPS o HTTP loopback, sin credenciales/rutas; vacíos generan mismo origen. La entrega comprobada utiliza un origen compartido de sesión/CSRF para autenticación y API: el build rechaza valores diferentes. Separarlos requiere diseñar un bootstrap CSRF por servicio con el despliegue real. Las peticiones usan credentials:include; el backend debe autorizar explícitamente el origen mediante PORTAL_ALLOWED_ORIGINS (CORS + CSRF), nunca comodín. SameSite=Lax requiere mismo sitio; dominios no relacionados/cookies de terceros necesitan diseño autorizado adicional. Revisar CSP connect-src, TLS y alcance de cookies en el servidor estático real. /portal/ en Django aplica connect-src 'self', frame-ancestors 'none', Referrer-Policy no-referrer y no permite imágenes: usar el build de mismo origen con esa ruta.

PORTAL_WIFI_LABEL y PORTAL_WELCOME_TEXT proporcionan parámetros públicos de presentación en /api/config. La etiqueta inicial es descriptiva, no un SSID verificado. Esa respuesta no expone reglas defensivas, SMTP, hashes ni secretos. No publicar la demo como servicio institucional.

## Vistas y privacidad

Se registra una carga de portal, primera entrada a cada sección y primera apertura de cada contenido por carga de página. Un mapa en memoria evita repetir por reaperturas/actualizaciones, sin almacenamiento persistente. Un fallo estadístico no bloquea navegación. El servidor deriva contexto/identidad; no recibe uid/tipo/IP confiados desde JSON. La primera carga puede ser anónima, sin reasignar retrospectivamente registros tras login.

El aviso explica IP/navegador/secciones/fecha/identidad seudónima, fines y acceso restringido. Las respuestas anónimas mantienen la cookie firmada HttpOnly de 90 días existente; borrar cookies/cambiar de navegador limita la deduplicación. La retención sigue configurable y solo se aplica mediante mantenimiento autorizado del Bloque 3. Este bloque no ejecuta retención ni borra registros anteriores.

## Pruebas y rendimiento

```powershell
.\.venv\Scripts\python.exe backend\manage.py test apps.accounts apps.content apps.analytics apps.portal --keepdb --verbosity 1
node --test captive-portal/tests/portal.test.cjs
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe backend\manage.py spectacular --validate --file docs\arquitectura\openapi.yaml
# Con backend iniciado
.\.venv\Scripts\python.exe scripts\smoke_portal_http.py
.\.venv\Scripts\python.exe scripts\measure_portal.py --connections 200
```

El smoke crea una encuesta DEMO propia, registra una participación, comprueba duplicación/vistas/estadísticas y elimina lógicamente esa encuesta. Conserva historial/respuestas. No modifica categorías/usuarios/configuración/contenidos anteriores. Los tests backend usan test_portalinfo separada y conservada con --keepdb; los de DOM simulan JSON. Las pruebas Playwright adicionales usan Chrome real y servicios locales.

RENDIMIENTO_FINAL.json conserva la medición con Waitress local y conexiones PostgreSQL reutilizables: 200/200 peticiones HTML correctas; ráfaga API con 60 respuestas 200 y 140 cuotas 429. Los picos activos observados fueron 194 y 199, sin redondearlos a 200 simultáneos. A 5 peticiones/s durante 5 s: 25/25 correctas. RENDIMIENTO_BLOQUE_4.json conserva los rechazos anteriores de runserver y RENDIMIENTO_WSGI_INICIAL.json la medición anterior a reutilizar conexiones. No se ocultan errores ni se desactivan cuotas. RNF-03 permanece parcial, sin aceptación institucional.

Cinco peticiones secuenciales por endpoint en la medición final: medianas API 9,095–34,391 ms y máximo 35,936 ms. HTML: mediana HTTP 1,499 ms, máximo 4,801 ms. Son transferencias locales, no renderizado, WiFi universitaria ni carga completa móvil. Muestra pequeña, Windows, sin TLS/carga institucional sostenida. RF-07/RNF-01/02/03 no se certifican mediante esos tiempos.

La revisión final usa Chrome 157.0.8103.39 y Playwright: sin desplazamiento horizontal en 360/390/480/768/1280 px, identificación WiFi visible, teclado/foco, login con fallo editorial, encuesta real y descargas. Capturas privadas en .local/capturas y resultados en NAVEGADOR_FINAL.json. Quedan pendientes Android/iOS físicos, WebViews, lector de pantalla, contraste/zoom exhaustivo y certificación WCAG/Manual de Identidad.

## Cierre local y pendientes institucionales

Portal local funcional, contratos/OpenAPI, artefacto ligero, cuentas separadas, votos/estadísticas conectados. Pendientes: servidor de producción/caché compartida, 200 conexiones sin rechazos, TLS/Docker/backup/restore, visual/dispositivos/accesibilidad/Manual de Identidad y contratos AGA_AUTH/pfSense/SMTP. No se modifica una red real para resolver esas dependencias.
