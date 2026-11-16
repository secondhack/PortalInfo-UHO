"""Download official PyPI wheels with hash validation and resumable local files."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request
import time

target=Path(__file__).resolve().parent.parent/'.local'/'wheels'
target.mkdir(parents=True,exist_ok=True)

def download(package):
    name,version=package
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=30) as response:
        metadata=json.load(response)
    wheel=next(x for x in metadata['urls'] if x['filename'].endswith('.whl'))
    path=target/wheel['filename']
    for attempt in range(6):
        if path.exists() and path.stat().st_size == wheel['size']:
            break
        offset=path.stat().st_size if path.exists() else 0
        try:
            request=urllib.request.Request(wheel['url'],headers={'Range':f'bytes={offset}-','User-Agent':'PortalInfo-local-setup'})
            with urllib.request.urlopen(request,timeout=30) as response:
                mode='ab' if response.status==206 else 'wb'
                with path.open(mode) as file:
                    while chunk:=response.read1(65536):
                        file.write(chunk)
            print(name,'downloaded',path.stat().st_size,flush=True)
        except (OSError,TimeoutError) as exc:
            print(name,'retry',attempt+1,type(exc).__name__,flush=True)
            time.sleep(1)
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=wheel['digests']['sha256']:
        raise RuntimeError(f'{name}: incomplete download or hash mismatch')
    print(name,'SHA256 verified',flush=True)

with ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(download,[('django-filter','25.2'),('django-cors-headers','4.9.0'),('drf-spectacular-sidecar','2026.10.1')]))
