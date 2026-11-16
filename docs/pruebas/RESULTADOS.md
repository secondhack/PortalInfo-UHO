# Resultados finales · Entrega local del Bloque 5

14 de noviembre de 2026, America/Havana. **173 pruebas automatizadas aprobadas, 0 fallidas y 0 omitidas en las suites finales:** 118 Django/PostgreSQL, 26 React/Vitest, 17 portal/DOM y 12 Playwright/Chrome. Se cuentan casos únicos, sin sumar repeticiones. Otras 29 comprobaciones HTTP reales se informan aparte; las cuotas/mediciones de carga no se convierten en pruebas funcionales aprobadas.

| Ejecución comprobada | Resultado final |
|---|---|
| Regresión inicial antes de cambios | 109 backend, 21 React y 17 portal aprobadas |
| probar_sistema.ps1: Django completo | 118 aprobadas en 78,012 s; test_portalinfo reutilizada/conservada con --keepdb |
| React/Vitest | 26 aprobadas, cuatro archivos, 3,94 s |
| Portal/DOM nativo | 17 aprobadas en 1,424 s |
| Playwright/Chrome 157.0.8103.39 | 12 aprobadas, 0 omitidas/inesperadas/flaky, 42,7 s; JSON en NAVEGADOR_FINAL.json |
| Build React | Correcto, 61 módulos; main 338,39 kB / 104,19 gzip; charts 175,37 kB / 61,17 gzip; CSS 11,50 kB / 3,28 gzip |
| Build portal y comprobador independiente | 24539 bytes sin gzip, límite 204800 |
| check / makemigrations --check --dry-run / migrate --check | Correctos; 36 migraciones aplicadas, ninguna nueva |
| OpenAPI spectacular --validate | Correcto, sin avisos/errores de generación |
| pip check / npm ls --depth=0 | Dependencias coherentes; Waitress y Playwright instalados localmente |
| verificar_entorno y scripts iniciar_* | Comprobados con PowerShell 5, rutas relativas, conexión DB y arranque real; no admin ni cambio global de política |
| smoke_final_http.py | 29 comprobaciones reales correctas, datos propios; doce exportaciones analizadas; E2E_FINAL.json |
| Escáner de secretos | Sin valores reales de secretos locales en archivos entregables; no se muestran credenciales |
| Respaldo | pg_dump custom de 142317 bytes en .local/backups; catálogo pg_restore --list válido |
| Guardia de restauración | Base actual rechazada antes de crear/restaurar; no se ejecutó restauración real |

## Cobertura y correcciones comprobadas

Todas las regresiones de bloques anteriores permanecen. Casos nuevos: login concurrente desde misma IP comparte cuota PostgreSQL, Cache-Control privado, entradas acotadas, APP_ENV desconocido rechazado en vez de activar demo, vigencia predeterminada configurable/preservación al editar, rango de días/fecha extrema rechazado, respuestas tardías ignoradas, Escape con cierre vigente, error de conexión sin reintentar escrituras y selección de vigencia por defecto en React, logout de sesión inválida con CSRF y fin de indicador de carga tras un error.

Navegador real: 18 rutas administrativas y pestañas de estadísticas sin excepciones JavaScript ni API administrativas fallidas; formularios móviles 360/480/768; portal sin desbordamiento a 360/390/480/768/1280 y WiFi visible; acceso denegado a Gestor para auditoría/estadísticas; login/logout con API editorial bloqueada; encuesta simple/múltiple/abierta enviada desde formulario y resultados comprobados; descargas CSV/PDF; teclado/foco. Capturas privadas en .local/capturas; se inspeccionaron panel, portal, usuarios, configuración, cola, logs, seguridad y encuesta. No se utilizaron perfiles habituales del navegador ni se subieron capturas.

HTTP integral: Superadmin creó Gestor y concesiones, Gestor guardó/envíó noticia, Admin recibió notificación/correo y aprobó, visitante registró vista y dashboard, segunda revisión conservó publicación anterior hasta aprobarse, encuesta real y resultados/exportaciones/auditoría/logout. Última ejecución creó solo IDs 56/57 y su Gestor propio ID 5; retiró lógicamente esos contenidos y desactivó ese usuario, conservando historial/respuestas. Las pruebas de navegador crearon también sus propias encuestas DEMO y las retiraron lógicamente al terminar. No se modificaron contenidos/cuentas anteriores para limpiar pruebas; la preferencia de correo se restauró si no cambió concurrentemente.

## Rendimiento final observado

RENDIMIENTO_FINAL.json: Windows 10.0.19041, Intel Family 6 Model 60, cuatro CPU lógicas, Python 3.11.9, Waitress 3.0.2 (ocho hilos, backlog/connection_limit 256), PostgreSQL 16 local con CONN_MAX_AGE=60 y health checks. Solo loopback numérico, sin TLS/radio/redirecciones/identidades falsificadas. Una ráfaga por endpoint, fase regulada de cinco segundos y cinco peticiones/s. Los límites de API siguen activos.

| Medición | Resultado |
|---|---|
| HTML HTTP secuencial, cinco muestras | 5/5 HTTP 200; mediana 1,499 ms, máximo 4,801 ms |
| API secuencial, cinco por endpoint | Todas HTTP 200; medianas 9,095–34,391 ms, máximo 35,936 ms |
| Noticias a 5 peticiones/s, 5 s | 25/25 HTTP 200; mediana 22,950 ms, p95 33,281 ms; pico activo 1 |
| Ráfaga de 200 peticiones HTML | 200 HTTP 200; p95 186,906 ms, máximo 195,938 ms; pico activo observado 194 |
| Ráfaga de 200 peticiones API | 60 HTTP 200 y 140 HTTP 429 por cuota; máximo de respuestas correctas 409,121 ms; pico activo observado 199 |

No hubo errores de conexión en la medición final. Se programan 200 clientes por ráfaga y se informan los picos medidos, sin afirmar 200 simultáneos cuando no se observaron. Los 429 no equivalen a usuarios atendidos ni se ocultan; p95 de todos los intentos API, incluidos bloqueos, fue 669,453 ms. La fase regulada no representa 200 usuarios concurrentes. RNF-03 queda parcial: falta validación sostenida multiusuario/IP institucional. Las medidas HTTP locales no certifican RF-07/RNF-01 de carga completa móvil ni latencia en producción.

Se conservan RENDIMIENTO_BLOQUE_4.json (rechazos de runserver) y RENDIMIENTO_WSGI_INICIAL.json (antes de reutilizar conexiones). La mejora de servidor/conexiones no borra resultados negativos anteriores.

## Incidencias resueltas y verificaciones no ejecutadas

- Con CONN_MAX_AGE=60 los 116 tests de una ejecución pasaron, pero la retirada automática de su base falló por dos conexiones de hilos aún abiertas. Se corrigió cierre explícito en ambas pruebas concurrentes. La suite final de 117 terminó correctamente con --keepdb; se conserva la base de pruebas en vez de borrar bases. Log de incidencia privado en .local/logs/pruebas-conexiones-incidencia.log.
- Vite no pudo optimizar dependencias dentro del sandbox por lectura de directorios superiores: se inició con lectura autorizada fuera de ese sandbox. La terminal normal de VS Code funciona con los scripts; no se modificaron proyectos ajenos.
- La detección inicial no incluía Chrome de Program Files (x86). Se amplió, se detuvo la descarga adicional y se ejecutó Chrome instalado con perfil aislado en .local.
- La revisión de capturas detectó WiFi oculto en móvil, etiqueta DEMO ambigua y tablas demasiado estrechas; se corrigieron y las 12 pruebas de navegador volvieron a pasar.
- Los avisos use client de React Router son benignos y no impiden compilar; no hay imports rotos ni chunks por encima del aviso previo.

No ejecutadas por falta de entorno/contrato o alcance institucional: AGA_AUTH/pfSense/SMTP/SIGENU/ASSET reales, Docker/TLS/Linux/Nginx/Gunicorn, restauración real, Android/iOS/WebViews físicos, lector de pantalla/contraste/zoom exhaustivos, aceptación WCAG/Manual de Identidad y carga institucional multiusuario/IP. No se presentan como aprobadas ni como omitidas silenciosamente del conteo de suites automatizadas.

PostgreSQL principal y sus datos se conservan; no se reinició el clúster ni aplicó retención/borrado físico. La base de pruebas se conserva separada con --keepdb. La aplicación permanece exclusivamente local, sin GitHub/GitLab, publicación, cuentas externas o pipelines. Guía completa: docs/manuales/COMO_PROBAR_EN_VSCODE.md; informe: docs/arquitectura/ENTREGA_FINAL.md.

---
# Historial de resultados · Bloque 4

14 de noviembre de 2026, America/Havana. **147 pruebas funcionales aprobadas, 0 fallidas en las suites finales: 109 Django/PostgreSQL, 21 React y 17 portal/DOM.** Se incluyen regresiones completas; no se suman repeticiones como pruebas distintas. El objetivo de carga de 200 conexiones NO se superó en runserver: se informa por separado y no se cuenta como prueba funcional aprobada.

| Verificación ejecutada | Resultado |
|---|---|
| Regresión antes de modificar código | 93 backend aprobadas en 47,445 s; 21 React aprobadas |
| Suite backend final apps.accounts apps.content apps.analytics apps.portal | 109 aprobadas en 78,263 s; incluye 16 nuevas de PortalTests |
| node --test captive-portal/tests/portal.test.cjs | 17 aprobadas en 1,690 s |
| npm.cmd --prefix frontend test | 21 aprobadas, cuatro archivos, 5,19 s |
| node captive-portal/build.mjs | dist/index.html autónomo: 24370 bytes sin gzip, límite 204800 |
| scripts/check_portal_size.py | Tamaño independiente dentro del presupuesto |
| npm.cmd --prefix frontend run build | Correcto; 60 módulos; main 337,38 kB, charts 175,37 kB, CSS 11,42 kB |
| manage.py check / makemigrations --check --dry-run | Sin incidencias / sin cambios; cero migraciones nuevas |
| spectacular --validate | OpenAPI actualizado sin avisos/errores de generación |
| pip check | No broken requirements found |
| seed_portal_demo | Tres visitantes ficticios privados creados; idempotencia/no sobrescritura/producción bloqueada comprobadas en tests |
| scripts/smoke_portal_http.py | Correcto contra Django/PostgreSQL reales: HTML, sesión, permisos, categorías, votos, duplicados, vistas, resultados/estadísticas, logout y cookie anterior |

Backend: visitante separado de User/roles, credenciales correctas/incorrectas, CSRF/origen malicioso, bloqueo configurado/expiración, sesión desconocida/vencida/revocada, logout y cookie antigua inválida sin perder CMS, proveedor institucional 503 sin red, contenido pendiente/vencido/oculto, sección deshabilitada, descubrimiento/metadatos sin contenidos, genérico, identidad no falsificable en vistas y encuesta autenticada con deduplicación. Excepción editorial simulada: 500 en noticias mientras HTML y login siguen operativos.

DOM: HTML estático sin CDN/peso, seis tipos y navegación, categoría nueva/secciones retiradas tras actualizar, login con API caída o petición pendiente, escape de texto, enlaces seguros, vistas únicas por carga y fallos estadísticos no bloqueantes, encuesta simple/múltiple/abierta/externa, obligatorios y errores del servidor conservando respuestas, autenticación previa al voto sin perder borrador, doble clic, login/logout/429, alternativa XHR sin fetch/Promise/AbortController, estructura responsive/semántica accesible y timeout editorial con abort. JSDOM no calcula geometría real ni acredita renderizado/accesibilidad de navegador.

HTTP real: se creó la encuesta DEMO propia ID 50, se aprobó, se registró una participación con dos tipos de selección y texto abierto, se rechazó duplicado, se registraron vistas y se consultaron resultados/estadísticas desde el CMS. Se eliminó lógicamente solo esa encuesta al terminar; permanecen historial, respuestas y auditoría. No se cambiaron configuración, categorías, usuarios o contenidos anteriores. No se consultó SMTP/AGA_AUTH/pfSense ni se modificó la red.

## Mediciones de rendimiento · resultado y límites

Herramienta reproducible: scripts/measure_portal.py, Python 3.11.9 http.client/ThreadPoolExecutor/Barrier. Windows 10.0.19041, Intel Family 6 Model 60, cuatro CPU lógicas, PostgreSQL 16 y Django 5.2.19 runserver local (cola de aceptación 10). Sin TLS, red móvil, renderizado de navegador ni WSGI de producción. Solo se permiten conexiones loopback numéricas, sin redirecciones. Datos íntegros: RENDIMIENTO_BLOQUE_4.json.

| Medición | Resultado observado |
|---|---|
| HTML secuencial, cinco peticiones | Mediana 2,631 ms; máximo 80,519 ms; 5/5 HTTP 200 |
| API secuencial, cinco por endpoint | Medianas 33,991–42,322 ms; máximo 63,758 ms; todas HTTP 200 |
| Ráfaga de 200 conexiones independientes al HTML | 68 HTTP 200; 132 ConnectionResetError; p95 de todos los intentos 598,615 ms |
| Ráfaga de 200 conexiones independientes a noticias | 66 HTTP 200; 134 ConnectionResetError; p95 de todos los intentos 1350,644 ms |

La barrera inicia 200 clientes juntos; aceptación/colas/límites del SO forman parte del resultado. No se ocultaron errores ni se desactivó rate limiting. No se atribuyen todos los rechazos a una capa sin un diagnóstico adicional. **RNF-03 permanece pendiente/no superado aquí**. El tamaño sí cumple RNF-04. La muestra API es limitada/loopback: no certifica RNF-02 en producción, ni el tiempo HTTP certifica RF-07/RNF-01 de carga completa móvil 1–2 segundos.

## Incidencias y pendientes

- Una prueba de caída editorial obtenía 404 porque no había creado la categoría antes de provocar el fallo: se corrigió el fixture y se comprobó el 500 esperado con login operativo.
- Las pruebas DOM detectaron que el helper de mensajes sustituía clases de estilo: se corrigió para conservarlas y alternar solo error; las encuestas/estados pasan.
- La ráfaga de 200 conexiones reveló rechazos de runserver. Se conserva como resultado negativo; dimensionamiento/despliegue WSGI y repetición institucional siguen pendientes.
- Vite conserva los avisos benignos de directivas use client de React Router; compila correctamente, sin aviso de chunk grande.
- No hay navegador instalado ni herramienta de navegador conectada: no se realizaron capturas ni pruebas geométricas reales 360–480 px, teclado/contraste/WCAG, Android/iOS/WebViews o Manual de Identidad. No se presentan como aprobadas.
- Pendientes institucionales: AGA_AUTH/pfSense reales, SMTP, TLS/Docker/Linux/WSGI/Nginx, caché compartida, backups/restore y carga sostenida. El aislamiento editorial no equivale a disponibilidad cuando cae todo Django/PostgreSQL.

No se añadieron migraciones, reinició PostgreSQL ni aplicó retención/borrado físico. Los servidores QA propios se detienen al concluir. Comandos/guía en README y docs/manuales/PORTAL_CAUTIVO.md; informe obligatorio en docs/arquitectura/ENTREGA_BLOQUE_4.md.

---

# Historial de resultados · Bloque 3

14 de noviembre de 2026, America/Havana. **114 pruebas aprobadas, 0 fallidas en la ejecución final: 93 Django/PostgreSQL y 21 React.** Incluye todas las regresiones de los bloques anteriores. Las 93 se distribuyen en 24 de base/seguridad, 36 CMS y 33 administrativas/analítica; las 21 frontend incluyen ocho nuevas. No se suman repeticiones como pruebas distintas.

| Verificación ejecutada | Resultado |
|---|---|
| Estado inicial: tests apps.accounts apps.content | 60 aprobadas en PostgreSQL |
| Estado inicial: npm test | 13 aprobadas |
| Suite conjunta final: manage.py test apps.accounts apps.content apps.analytics --verbosity 1 | 93 aprobadas en 46,796 s; base test_portalinfo creada, migrada y retirada por Django |
| npm.cmd --prefix frontend test | Cuatro archivos, 21 aprobadas |
| npm.cmd --prefix frontend run build | Correcto, 60 módulos; JS principal 337,38 kB (103,65 gzip), gráficos 175,37 kB (61,17 gzip), CSS 11,42 kB |
| manage.py check | Sin incidencias |
| makemigrations --check --dry-run | No changes detected |
| migrate | Ocho migraciones incrementales aplicadas, preservando las 28 anteriores |
| spectacular --validate --file docs/arquitectura/openapi.yaml | OpenAPI 3.0.3 válido, sin avisos/errores de generación |
| pip check | No broken requirements found |
| seed_demo --with-activity | Actividad DEMO identificada, tres señales nuevas; los tests verifican repetición sin duplicados ni cambios en datos manuales |
| maintain_logs sobre la base de trabajo | SIMULACIÓN; cero candidatos, ningún dato eliminado |
| deliver_notifications --limit 100 tras el smoke | Cero pendientes; las tres entregas locales ya estaban enviadas |
| scripts/smoke_administration_http.py | Login/roles, envío/decisión repetida, correo local, contador/lectura, acceso/vista, métricas/logs/señales/resultados y doce exportaciones reales; correcto |
| CSV/PDF HTTP | Seis tipos por dos formatos; CSV analizado y PDF abierto con pypdf |

Aprobaciones/notificaciones: destinatarios correctos, aislamiento de inbox, lectura y fecha idempotente, eventos al enviar/aprobar/rechazar/expirar, solicitudes/propuestas estables, conservación de versión aprobada, concurrencia con dos conexiones PostgreSQL y una sola publicación/notificación, envío local después del commit, error seguro de proveedor y reintento sin duplicar entregas ya enviadas.

Métricas/privacidad: contexto del servidor y proxies explícitos, rechazo de identidades de JSON, bloqueo de contenido privado/no visible, CSRF y throttling, períodos/zonas/agrupaciones, datos DEMO separados por defecto, totales SQL y permisos. El dashboard del Gestor excluye logs globales. Los participantes seudónimos se diferencian de envíos/versiones, la selección múltiple puede sumar 200 %, y las respuestas abiertas se paginan sin identificadores de votantes.

Señales/auditoría/reportes: reglas positivas y negativas, historia previa para actividad inusual, deduplicación de señales, revisión humana sin bloquear cuentas, configuración reservada, antes/después sin secretos, inmutabilidad por API, retención autorizada solo en tests efímeros, CSV UTF-8/fórmulas, filtros y fuentes aplicados, PDF válido y paginado, límite PDF explícito y permisos por reporte. La lista de 15 notificaciones no aumenta las consultas respecto a una sola fila.

React: campana/contador/lectura, polling 30 s y limpieza, cola/comparación/rechazo, datos enviados al gráfico y alternativa tabular, descarga CSV/PDF con filtros/error, revisión de alertas, auditoría/detalle y resultados abiertos. Se prueban componentes con API simulada y constructor de gráficos controlado; no equivalen a una inspección visual real del canvas en navegador. El smoke HTTP usa Django y PostgreSQL reales.

Incidencias corregidas:

- Un test intentaba enviar un diccionario anidado como multipart: se corrigió a JSON; el filtro de auditoría ya funcionaba.
- Un test imponía seis consultas sin contar toda la sesión: se sustituyó por la comprobación pertinente, que las consultas no crezcan por fila (7 en ambos tamaños).
- El primer bundle superaba 500 kB: Chart.js quedó en chunk separado, sin ocultar el umbral.
- Vite necesitó ejecutar el optimizador fuera del sandbox Windows al cambiar lockfile, igual que en bloques anteriores. Compilación/tests locales funcionan con configLoader native.
- El correo y la actividad inicialmente faltaban: se completaron con proveedor local, salida persistente y endpoints reales. No se contactó SMTP ni AGA_AUTH.

La comprobación HTTP creó y eliminó lógicamente solo su contenido DEMO propio (ID 49), conservando auditoría y tres mensajes locales en .local/mail. Restauró la preferencia previa de correo. No marcó ni cambió contenido ajeno. No se aplicó retención real ni se reinició PostgreSQL.

Sin verificar: navegador/revisión visual/WCAG/Manual de Identidad, carga de 200 conexiones, presupuestos de latencia/tamaño del portal, Docker/TLS/Gunicorn/Nginx e integración real SMTP/AGA_AUTH/pfSense. El correo SMTP conserva la limitación de entrega al menos una vez ante caída después de aceptación; varios workers requieren caché compartida. Estas limitaciones no se presentan como pruebas aprobadas.

Comandos en README; semántica de métricas, privacidad y operación en BLOQUE_3.md. Los servidores de QA se detienen al concluir; la instancia PostgreSQL y sus datos se conservan.

---
# Historial de resultados · Bloque 2

14 de noviembre de 2026, America/Havana. **73 pruebas aprobadas, 0 fallidas en las suites finales: 60 Django/PostgreSQL y 13 React.** Las 60 incluyen 24 de base y 36 CMS. Las 13 incluyen 6 previas y 7 nuevas. No se suman las repeticiones de ejecución.

| Verificación ejecutada | Resultado final |
|---|---|
| manage.py test apps.accounts apps.content --verbosity 1 | 60 aprobadas en 38,736 s; PostgreSQL test_portalinfo creada/migrada/retirada por el runner |
| npm.cmd --prefix frontend test | 3 archivos, 13 aprobadas |
| npm.cmd --prefix frontend run build | 49 módulos; JS 306,78 kB (96,08 kB gzip), CSS 9,52 kB; compilación correcta |
| manage.py check | Sin incidencias |
| makemigrations --check --dry-run | No changes detected |
| migrate | Cinco migraciones incrementales aplicadas; las 23 anteriores se conservan |
| spectacular --validate --file docs/arquitectura/openapi.yaml | OpenAPI 3.0.3 válido, rutas literales de cinco módulos y ruta dinámica documentadas |
| pip check | No broken requirements found |
| seed_demo y check_demo_seed | 42 contenidos nuevos inicialmente, 0 al repetir; sin sobrescribir datos |
| register_expirations dos veces | 6 expiraciones nuevas, luego 0; ocultamiento independiente del proceso |
| scripts/smoke_content_http.py | Seis flujos HTTP reales: CRUD, envío/revisión, publicación, edición, switch, historial, voto, resultado y eliminación lógica |
| Vite /content/noticias, módulo React y proxy /api/noticias | HTTP 200 |
| Swagger, recurso JS local y siete consultas públicas | HTTP 200; OpenAPI en ejecución incluye las cinco rutas literales |
| Trazabilidad | 84 identificadores originales, 27 RF con evidencia del Bloque 2 |

Cobertura CMS: CRUD de news/event/notice/service/survey/generic, filtros de área/estado/fechas/evento, búsqueda/orden/paginación, permisos por rol/operación/categoría, categorías nuevas/renombradas, slugs reservados y base estables, revisión pendiente sin alterar aprobación anterior, correcciones directas de Admin, rechazo motivado, solicitudes obsoletas, eliminación lógica, límites/campos dinámicos, máximo visible y advertencia no bloqueante, seis modalidades de vigencia, expiración idempotente, switches y secciones deshabilitadas.

Encuestas: límites de preguntas/opciones/abiertas, externas, archivado de definiciones, selección simple/múltiple/texto, duplicados, preguntas/opciones ajenas, cardinalidad, obligatoriedad, encuestas inactivas/fuera del máximo, persistencia/porcentajes/textos restringidos, CSRF anónimo/autenticado, autenticación requerida y restricciones PostgreSQL. El throttle resiste cambios de X-Forwarded-For. Cinco publicaciones se consultan con un máximo de tres consultas SQL en el GET probado; no equivale a carga concurrente.

React: guardar/enviar noticia con advertencia, conservar formulario ante error, bloquear doble envío, editor de preguntas/opciones/orden/obligatoriedad/límites, filtros/switch/eliminación confirmada, Escape/retorno de foco y texto escapado/enlaces seguros. Los componentes usan API simulada; smoke_content_http comprueba API y PostgreSQL reales. No hay navegador conectado para inspección visual interactiva.

Incidencias corregidas: en instalación vacía, seed_demo no asignaba content_type; se corrigió y se verificó con FreshSeedTests. Además, cuatro fallos iniciales frontend por etiquetas que incluían contadores y mocks pendientes entre tests; se corrigieron nombres accesibles y reinicio de mocks sin omitir pruebas. Se ajustó la prueba histórica de visibilidad a las versiones aprobadas. Suites backend iniciales 51/57/58/59 pasaron; la final de 60 también. Se corrigió además una conversión de texto UTF-8 por PowerShell en documentación, sin cambios de datos.

Los seis contenidos de comprobación HTTP se crearon como DEMO y se eliminaron lógicamente. Su historial y una participación real de prueba se conservan, sin afectar datos anteriores. Los ejemplos semilla no reciben respuestas simuladas.

Límites: revisión visual/WCAG/Manual de Identidad, carga concurrente, Docker, TLS/Gunicorn/Nginx e integraciones institucionales siguen sin verificar. El voto anónimo puede repetirse al borrar cookies/cambiar navegador; varios workers requieren caché compartida. No se identifica una persona por IP. Campana, analítica integral y pfSense pertenecen a bloques posteriores.

Comandos en README y contratos en BLOQUE_2.md. Los servidores de QA se detienen al terminar; la instancia PostgreSQL y sus datos se conservan. No se modificaron requisitos originales ni se reinició el clúster.

---
# Historial de resultados · Bloque 1

14 de noviembre de 2026, America/Havana. **24 tests Django + 6 tests React aprobados; 0 fallidos en la ejecución final.** PostgreSQL real, sin SQLite.

| Comprobación ejecutada | Resultado |
|---|---|
| Extracción PDF | 24 folios, 61 RF y 23 RNF; transcripción y trazabilidad generadas |
| Python compileall | Backend y scripts sin errores de sintaxis |
| PostgreSQL pg_isready | Instancia aislada 127.0.0.1:55432 acepta conexiones |
| manage.py check | Sin incidencias |
| manage.py migrate | 8 migraciones iniciales del proyecto + 15 de Django aplicadas |
| manage.py makemigrations --check --dry-run | No changes detected |
| seed_demo + check_demo_seed | Tres cuentas demo; repetir conserva usuarios, hashes y catálogos |
| manage.py test apps.accounts --verbosity 2 | 24 aprobados en 20,863 s; test_portalinfo creada, migrada y retirada por Django |
| npm.cmd test | 2 archivos, 6 tests aprobados |
| npm.cmd run build | Correcto; 45 módulos; JS 281,66 kB (89,60 kB gzip), CSS 7,45 kB |
| manage.py spectacular --validate --file docs/arquitectura/openapi.yaml | OpenAPI 3.0.3 válido, sin avisos/errores de generación |
| pip check | No broken requirements found |
| Arranque producción con AUTH_PROVIDER=demo | Rechazado mediante ImproperlyConfigured, como corresponde |
| Django runserver 127.0.0.1:8010 --noreload | Arranque correcto |
| Vite 127.0.0.1:5174 | Arranque correcto; documento y módulo React HTTP 200 |
| scripts/smoke_http.py | Login real con CSRF, sesión, once consultas API, logout y React HTTP 200 |
| Swagger HTML y swagger-ui-bundle.js local | HTTP 200, sin dependencia de CDN |
| Proxy Vite /api/health/ | HTTP 200 hasta Django |

Cobertura backend: PostgreSQL y migraciones, login de tres roles, credenciales incorrectas y usuario inexistente, autorización previa, desactivación con sesión existente, logout con cookie antigua, bloqueo por IP, CSRF de login, endpoints protegidos, Gestor ante categorías propias/ajenas y usuarios, concesiones por operación/categoría/asignación, escalada Admin, alta/edición de usuarios, dominio institucional, contraseñas débiles, protección del Superadmin, nomencladores CRUD e integridad, configuración persistente y límites, categorías y configuración pública, auditoría restringida y sin escritura por API, visibilidad editorial/temporal independiente, contadores y búsqueda, proveedor demo prohibido en producción y Swagger.

Cobertura React: login y errores, dashboard con datos de API, alta de usuario, configuración, CSRF y renovación tras login, validación del servidor. Pruebas de componentes con API simulada; smoke_http comprueba además la API real. No equivalen a una sesión visual completa de navegador.

Incidencias resueltas:

- npm.ps1 bloqueado por PowerShell: uso de npm.cmd.
- PostgreSQL existente 5432 y aplicaciones 8000/5173: clúster independiente 55432 y puertos 8010/5174 sin interrumpirlos.
- pg_ctl necesitó ejecución fuera del sandbox para crear el proceso Windows.
- Timeouts PyPI, ECONNRESET npm y permisos de caché. Se copiaron distribuciones Python ya instaladas sin modificar su entorno de origen, y se instalaron los paquetes faltantes desde wheels PyPI. requirements.lock.txt registra versiones portables sin rutas personales.
- psycopg-binary no se resolvió inicialmente. requirements.txt admite psycopg puro con libpq de PostgreSQL; el entorno validado dispone también de extensión binaria 3.3.8 reutilizada localmente.
- esbuild no podía leer un directorio antecesor bajo sandbox. ConfigLoader native permite tests/build; Vite necesitó ejecución fuera del sandbox para optimizar dependencias.
- DEBUG heredado desactivaba estáticos pese al .env. PORTALINFO_DEBUG permite configuración propia; Swagger y su JS se comprobaron otra vez con HTTP 200.
- Diagnóstico inicial de producción falló por codificación subprocess en Windows; se repitió comprobando bytes y confirmó el rechazo requerido.

Avisos: React Router contiene directivas use client que Rollup ignora correctamente para la SPA. Django recuerda que runserver es solo desarrollo.

Límites: no hay herramienta de navegador para inspección visual; tampoco Docker detectado. Sin validación de Docker/Nginx/Gunicorn, AGA_AUTH, SMTP, carga concurrente, Manual de Identidad Visual ni WCAG AA. Retención se almacena, pero su aplicación programada está pendiente. No se verifican requisitos completos del SRS cuando solo se cubre su base administrativa.

Comandos reproducibles en README. Entorno virtual, credenciales y datos PostgreSQL fuera del control de versiones. Los servidores de desarrollo usados para comprobar se detienen al concluir; los scripts permiten reiniciarlos.
