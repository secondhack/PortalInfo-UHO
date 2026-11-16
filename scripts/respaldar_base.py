"""Create a new private pg_dump archive; refuses overwrites and external paths."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from postgres_tools import root,configuration,tool,child_environment,connection_args

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path)
args=parser.parse_args()
target=(args.output or root/'.local/backups'/('portalinfo-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.dump')).resolve()
allowed=(root/'.local/backups').resolve()
if not target.is_relative_to(allowed):parser.error('El respaldo debe quedar dentro de .local/backups del proyecto.')
try:
    cfg=configuration()
    if cfg['DATABASE_HOST'] not in {'127.0.0.1','localhost','::1'}:raise RuntimeError('La utilidad de demostración solo respalda PostgreSQL local.')
    binary=tool('pg_dump');target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as archive:
        result=subprocess.run([binary,*connection_args(cfg),'--dbname',cfg['DATABASE_NAME'],'--format=custom','--no-owner','--no-acl'],
            stdout=archive,stderr=subprocess.PIPE,env=child_environment(cfg),timeout=120)
    if result.returncode:raise RuntimeError('pg_dump no completó el respaldo. No se modificó la base; revise la configuración local.')
    check=subprocess.run([tool('pg_restore'),'--list',str(target)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=30)
    if check.returncode:raise RuntimeError('El archivo no supera la lectura de catálogo pg_restore --list.')
    print('Respaldo creado y catálogo validado:',target.relative_to(root),'|',target.stat().st_size,'bytes. No se ha restaurado ni modificado la base.')
except FileExistsError:sys.exit('ERROR: el archivo ya existe; elija un nombre nuevo. No se sobrescribió.')
except Exception as error:sys.exit('ERROR: '+str(error) if isinstance(error,RuntimeError) else 'ERROR: respaldo no completado ('+type(error).__name__+').')
