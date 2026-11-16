"""Check actual local secret values against deliverable text, without displaying them."""
from pathlib import Path
import sys
from dotenv import dotenv_values

root=Path(__file__).resolve().parent.parent
values=dotenv_values(root/'.env')
secrets=[values.get(key,'') for key in ['SECRET_KEY','DATABASE_PASSWORD','EMAIL_HOST_PASSWORD']]
for name,separator in [('demo-credentials.txt','\t'),('portal-demo-credentials.txt',': ')]:
    source=root/'.local'/name
    if source.exists():
        secrets.extend(line.split(separator,1)[1] for line in source.read_text(encoding='utf-8').splitlines() if separator in line)
secrets=[value for value in secrets if value and len(value)>=8]
paths=[]
for folder in ['backend','frontend/src','frontend/dist','frontend/e2e','scripts','captive-portal','docs/arquitectura','docs/manuales','docs/pruebas']:
    paths.extend(p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in {'.py','.js','.jsx','.mjs','.cjs','.json','.yaml','.md','.txt','.html','.css','.ps1','.cmd','.conf'} and '__pycache__' not in p.parts and 'staticfiles' not in p.parts)
paths.extend([root/'README.md',root/'.env.example',root/'docker-compose.yml'])
matches=[]
for path in paths:
    text=path.read_text(encoding='utf-8-sig')
    if any(value in text for value in secrets):matches.append(str(path.relative_to(root)))
if matches:
    print('ERROR: posibles secretos locales en archivos entregables:',', '.join(matches))
    sys.exit(1)
print('Sin valores de secretos locales en',len(paths),'archivos entregables. No se muestran contraseñas ni tokens.')
