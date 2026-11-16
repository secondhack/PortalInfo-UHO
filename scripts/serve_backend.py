"""Bounded local WSGI server for the Windows demonstration; no admin/service install."""
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root/'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from waitress import serve

application = get_wsgi_application()
if settings.DEBUG:
    application = StaticFilesHandler(application)
print('PortalInfo UHO · WSGI local, 8 hilos, cola 256; Ctrl+C para detener.', flush=True)
print('API: http://127.0.0.1:8010/api/health/ | Portal: http://127.0.0.1:8010/portal/', flush=True)
serve(application, host='127.0.0.1', port=8010, threads=8, backlog=256, connection_limit=256,
      channel_timeout=30, max_request_body_size=2*1024*1024, max_request_header_size=16384,
      expose_tracebacks=False)
