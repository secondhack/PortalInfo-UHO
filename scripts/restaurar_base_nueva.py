"""Explicit restore to a NEW local database only. Never clean/drop/overwrite."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
from postgres_tools import root,configuration,tool,child_environment,connection_args

parser=argparse.ArgumentParser()
parser.add_argument('--archive',type=Path,required=True)
parser.add_argument('--target',required=True)
args=parser.parse_args()
archive=args.archive.resolve()
if not archive.is_relative_to((root/'.local/backups').resolve()) or not archive.is_file():parser.error('Seleccione un respaldo existente en .local/backups.')
if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}',args.target):parser.error('Nombre destino: letras minúsculas/números/guion bajo, empezando por letra.')
try:
    cfg=configuration()
    if args.target in {cfg['DATABASE_NAME'],'postgres','template0','template1'}:raise RuntimeError('Destino protegido; use un nombre de base nuevo y distinto.')
    if cfg['DATABASE_HOST'] not in {'127.0.0.1','localhost','::1'}:raise RuntimeError('La utilidad solo restaura contra PostgreSQL local.')
    binary=tool('pg_restore')
    listing=subprocess.run([binary,'--list',str(archive)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=30)
    if listing.returncode:raise RuntimeError('Respaldo no válido; no se creó ninguna base.')
    import psycopg
    from psycopg import sql
    with psycopg.connect(dbname='postgres',host=cfg['DATABASE_HOST'],port=cfg['DATABASE_PORT'],user=cfg['DATABASE_USER'],
            password=cfg['DATABASE_PASSWORD'],autocommit=True,connect_timeout=10) as connection:
        if connection.execute('SELECT 1 FROM pg_database WHERE datname=%s',(args.target,)).fetchone():
            raise RuntimeError('La base destino ya existe. Se rechaza sobrescribirla.')
        connection.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(args.target)))
    result=subprocess.run([binary,*connection_args(cfg),'--dbname',args.target,'--no-owner','--no-acl','--exit-on-error',str(archive)],
        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=child_environment(cfg),timeout=180)
    if result.returncode:raise RuntimeError('Restauración incompleta en la base NUEVA; se conserva para revisión. La base original no se modificó.')
    print('Restauración completada en la base nueva',args.target,'. No se cambió .env ni la base original.')
except Exception as error:sys.exit('ERROR: '+str(error) if isinstance(error,RuntimeError) else 'ERROR: restauración detenida ('+type(error).__name__+'); revise la configuración sin compartir secretos.')
