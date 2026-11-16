"""Local PostgreSQL client discovery, without putting passwords in arguments."""
import os
from pathlib import Path
import shutil
from dotenv import load_dotenv

root=Path(__file__).resolve().parent.parent


def configuration():
    load_dotenv(root/'.env')
    keys=['DATABASE_NAME','DATABASE_USER','DATABASE_PASSWORD','DATABASE_HOST','DATABASE_PORT']
    if any(not os.getenv(key) for key in keys):raise RuntimeError('Faltan parámetros PostgreSQL en .env.')
    return {key:os.environ[key] for key in keys}


def tool(name):
    suffix='.exe' if os.name=='nt' else ''
    for folder in [os.getenv('PG_BIN',''),r'C:\Program Files\PostgreSQL\16\bin']:
        if folder:
            candidate=Path(folder)/(name+suffix)
            if candidate.is_file():return str(candidate)
    candidate=shutil.which(name)
    if not candidate:raise RuntimeError('No se encuentra '+name+'. Configure PG_BIN con la carpeta bin de PostgreSQL.')
    return candidate


def child_environment(cfg):
    return dict(os.environ,PGPASSWORD=cfg['DATABASE_PASSWORD'],PGCONNECT_TIMEOUT='10')


def connection_args(cfg):
    return ['--host',cfg['DATABASE_HOST'],'--port',cfg['DATABASE_PORT'],'--username',cfg['DATABASE_USER']]
