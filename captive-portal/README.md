# Portal cautivo · Bloque 4

Portal funcional HTML5 + JavaScript nativo. Fuentes mantenibles en src/, artefacto autónomo en dist/index.html. El CMS React sigue separado.

```powershell
node captive-portal/build.mjs
.\.venv\Scripts\python.exe scripts/check_portal_size.py
.\.venv\Scripts\python.exe backend/manage.py seed_portal_demo
.\scripts\start-backend.cmd
```

Abrir http://127.0.0.1:8010/portal/. Credenciales ficticias privadas en .local/portal-demo-credentials.txt; nunca se incluyen en el HTML. No abrir con file://: necesita los servicios HTTP de sesión y contenidos.

El CSS contiene un subconjunto propio compatible con clases Bootstrap 5 (container/card/btn/form/nav), sin Bootstrap completo ni su JavaScript. Sin CDN, fuentes externas, React, imágenes, videos o adjuntos. Compila con esbuild ya instalado en frontend/node_modules; npm.cmd --prefix frontend ci si falta. El build falla por encima de 204800 bytes sin gzip; el comprobador Python mide independientemente.

Pruebas DOM: `node --test captive-portal/tests/portal.test.cjs`. Backend: `.venv\Scripts\python.exe backend\manage.py test apps.portal`. HTTP real: `.venv\Scripts\python.exe scripts\smoke_portal_http.py`. Medición local: `.venv\Scripts\python.exe scripts\measure_portal.py --connections 200`.

PORTAL_API_BASE/PORTAL_AUTH_BASE al compilar permiten fijar orígenes HTTPS (vacíos: mismo origen). Autenticación y contenidos son independientes; no se presupone ningún endpoint AGA_AUTH/pfSense. Guía: docs/manuales/PORTAL_CAUTIVO.md. El simulador no intercepta tráfico ni modifica Internet.
