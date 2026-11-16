"""Read-only local readiness check. Never prints .env values or connection errors."""
import argparse
import importlib.metadata
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--skip-database', action='store_true')
args = parser.parse_args()
if sys.version_info < (3, 11):
    sys.exit('ERROR: se necesita Python 3.11 o posterior.')
if not (root/'.env').is_file():
    sys.exit('ERROR: falta .env. Consulte docs/manuales/COMO_PROBAR_EN_VSCODE.md; no sobrescriba una configuración existente.')
for name in ['Django','djangorestframework','psycopg','django-cors-headers','django-filter','drf-spectacular','reportlab','waitress']:
    try: print(name + ' ' + importlib.metadata.version(name))
    except importlib.metadata.PackageNotFoundError:
        sys.exit('ERROR: faltan dependencias. Ejecute .venv\\Scripts\\python.exe -m pip install -r backend\\requirements-dev.txt')
sys.path.insert(0, str(root/'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    import django
    django.setup()
except Exception as error:
    sys.exit('ERROR: configuración no válida ('+type(error).__name__+'). Revise .env sin compartir secretos.')
from django.conf import settings
print('Python', sys.version.split()[0], '| configuración cargada; secretos ocultos')
if not args.skip_database:
    try:
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        with connection.cursor() as cursor:
            cursor.execute('SELECT version()')
            version = cursor.fetchone()[0].split(',')[0]
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        print(version)
        if pending:
            sys.exit('ERROR: hay migraciones pendientes. Inspeccione manage.py showmigrations antes de aplicarlas.')
        print('PostgreSQL conectado; migraciones al día.')
    except Exception as error:
        sys.exit('ERROR: no se pudo comprobar PostgreSQL ('+type(error).__name__+'). Revise host/puerto/.env o inicie solo el clúster del proyecto si está detenido.')
print('Entorno local preparado. Modo portal:', settings.PORTAL_AUTH_MODE)
