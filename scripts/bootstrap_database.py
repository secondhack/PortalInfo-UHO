from pathlib import Path
import secrets, subprocess
root=Path.cwd()
local=root/'.local'; local.mkdir(exist_ok=True)
password=secrets.token_urlsafe(32)
secret=secrets.token_urlsafe(64)
env=f'''APP_ENV=development
PORTALINFO_DEBUG=true
SECRET_KEY={secret}
AUTH_PROVIDER=demo
DATABASE_NAME=portalinfo
DATABASE_USER=portalinfo
DATABASE_PASSWORD={password}
DATABASE_HOST=127.0.0.1
DATABASE_PORT=55432
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
'''
if not (root/'.env').exists():
    (root/'.env').write_text(env,encoding='utf-8')
    pw=local/'init-password'; pw.write_text(password,encoding='utf-8')
    try:
        subprocess.run([r'C:\Program Files\PostgreSQL\16\bin\initdb.exe','-D',str(local/'postgres'),'-U','portalinfo','--pwfile='+str(pw),'--auth=scram-sha-256','--encoding=UTF8','--locale=C'],check=True)
    finally:
        pw.unlink(missing_ok=True)
else:
    print('.env existente conservado. No se reinicializa el clúster.')
