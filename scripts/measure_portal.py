"""Read-only local HTTP measurements; does not claim browser render/mobile timings.

200 worker threads synchronize at a barrier, each opens one independent connection.
Only numeric loopback addresses are allowed; redirects are refused.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from datetime import datetime, timezone
import http.client
import json
import os
from pathlib import Path
import platform
import statistics
import threading
import time
from urllib.parse import urlsplit

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://127.0.0.1:8010')
parser.add_argument('--connections', type=int, default=200)
parser.add_argument('--output', default=str(root/'docs/pruebas/RENDIMIENTO_LOCAL.json'))
parser.add_argument('--server-label', default='Servidor local declarado por el operador; no se certifica producción')
args = parser.parse_args()
url = urlsplit(args.base)
if url.scheme != 'http' or url.hostname not in ('127.0.0.1', '::1') or url.username or url.password or url.path not in ('', '/'):
    parser.error('Solo se admite HTTP loopback numérico, sin ruta/credenciales.')
if not 1 <= args.connections <= 200:
    parser.error('Máximo 200 conexiones locales.')


def request(path, barrier=None):
    connection = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=30)
    if barrier:
        barrier.wait(timeout=30)
    started = time.perf_counter()
    try:
        connection.request('GET', path, headers={'Connection':'close', 'Accept':'application/json'})
        response = connection.getresponse(); data = response.read()
        return {'status':response.status, 'ms':round((time.perf_counter()-started)*1000, 3), 'bytes':len(data)}
    except Exception as error:
        return {'status':'error:'+type(error).__name__, 'ms':round((time.perf_counter()-started)*1000, 3), 'bytes':0}
    finally:
        connection.close()


def summary(rows):
    times = sorted(row['ms'] for row in rows)
    return {'requests':len(rows), 'statuses':dict(Counter(str(row['status']) for row in rows)),
        'min_ms':times[0], 'median_ms':round(statistics.median(times), 3),
        'p95_ms':times[min(len(times)-1, int(len(times)*.95))], 'max_ms':times[-1],
        'max_response_bytes':max(row['bytes'] for row in rows)}


def concurrent(path):
    barrier = threading.Barrier(args.connections)
    with ThreadPoolExecutor(max_workers=args.connections) as pool:
        rows = list(pool.map(lambda _: request(path, barrier), range(args.connections)))
    return summary(rows)


result = {'timestamp_utc':datetime.now(timezone.utc).isoformat(), 'base':args.base,
    'tool':'Python stdlib http.client + ThreadPoolExecutor + Barrier; one TCP connection per request',
    'environment':{'platform':platform.platform(), 'cpu':platform.processor(), 'logical_cpus':os.cpu_count(),
        'python':platform.python_version(), 'server':args.server_label},
    'connections':args.connections, 'html_bytes':(root/'captive-portal/dist/index.html').stat().st_size,
    'normal':{path:summary([request(path) for _ in range(5)]) for path in
        ['/portal/','/api/config','/api/categorias?include_contents=false','/api/noticias','/api/eventos','/api/avisos','/api/servicios','/api/encuestas']},
    'concurrent_html':concurrent('/portal/'),
    'concurrent_api':concurrent('/api/noticias'),
    'limits':['Single loopback IP is subject to the normal API rate limit; 429 is recorded, never hidden.',
        'Development server, no TLS, no mobile radio/network, no browser rendering; does not certify RNF-01/02/03.',
        '200 client connections start together; server acceptance/queuing and OS limits are included.']}
Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=True, indent=2))
