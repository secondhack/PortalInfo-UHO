"""Optional offline fallback: copy selected installed distributions into this venv.

Only package RECORD entries within the supplied site-packages are read. The
source environment is never modified. Normal installation uses requirements.txt.
"""
import importlib.metadata
import shutil
import sys
from pathlib import Path

source = Path(sys.argv[1]).resolve()
target = Path(sys.prefix) / 'Lib' / 'site-packages'
selected = {'django','djangorestframework','drf-spectacular','psycopg','psycopg-binary',
    'python-dotenv','asgiref','sqlparse','tzdata','typing-extensions','uritemplate',
    'pyyaml','jsonschema','inflection','attrs','jsonschema-specifications','referencing','rpds-py'}
if len(sys.argv)>2:
    selected={name.lower().replace('_','-') for name in sys.argv[2:]}
for distribution in importlib.metadata.distributions(path=[str(source)]):
    name = distribution.metadata['Name'].lower().replace('_','-')
    if name not in selected:
        continue
    for relative in distribution.files or []:
        src = (source / relative).resolve()
        if not src.is_relative_to(source) or not src.is_file():
            continue
        dst = target / src.relative_to(source)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
    print(f'{distribution.metadata["Name"]}=={distribution.version}')
