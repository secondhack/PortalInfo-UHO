import os
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if os.name == 'nt':
    os.environ['PATH'] = r'C:\Program Files\PostgreSQL\16\bin;' + os.environ.get('PATH','')
from dotenv import load_dotenv
import psycopg
from psycopg import sql
load_dotenv(root/'.env')
with psycopg.connect(dbname='postgres',user=os.environ['DATABASE_USER'],password=os.environ['DATABASE_PASSWORD'],host=os.environ['DATABASE_HOST'],port=os.environ['DATABASE_PORT'],autocommit=True) as conn:
    name = os.environ['DATABASE_NAME']
    if not conn.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone():
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
print('Base del proyecto disponible; no se alteraron bases existentes.')
