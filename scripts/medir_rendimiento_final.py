"""Bounded loopback measurements: paced normal load plus one 200-connection burst.

No authentication, identity spoofing, retries, limiter bypass or remote redirects.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import http.client
import json
import os
from pathlib import Path
import platform
import statistics
import threading
import time
from urllib.parse import urlsplit

root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--base',default='http://127.0.0.1:8010')
parser.add_argument('--connections',type=int,default=200)
parser.add_argument('--rate',type=int,default=5)
parser.add_argument('--seconds',type=int,default=5)
args=parser.parse_args();url=urlsplit(args.base)
if url.scheme!='http' or url.hostname not in {'127.0.0.1','::1'} or url.username or url.password or url.path not in {'','/'} or url.query or url.fragment:
    parser.error('Solo HTTP loopback numérico, sin credenciales/ruta/query.')
if not 1<=args.connections<=200 or not 1<=args.rate<=5 or not 1<=args.seconds<=10:
    parser.error('Límites locales: 200 conexiones, 5 peticiones/segundo y 10 segundos por fase sostenida.')
active=0;peak=0;lock=threading.Lock()


def request(path,barrier=None,delay=0):
    global active,peak
    if delay>0:time.sleep(delay)
    if barrier:barrier.wait(timeout=20)
    with lock:active+=1;peak=max(peak,active)
    connection=http.client.HTTPConnection(url.hostname,url.port or 80,timeout=10)
    start=time.perf_counter()
    try:
        connection.request('GET',path,headers={'Connection':'close','User-Agent':'PortalInfo local bounded measurement'})
        response=connection.getresponse();body=response.read()
        return {'status':response.status,'ms':round((time.perf_counter()-start)*1000,3),'bytes':len(body)}
    except Exception as error:return {'status':type(error).__name__,'ms':round((time.perf_counter()-start)*1000,3),'bytes':0}
    finally:
        connection.close()
        with lock:active-=1


def summary(rows):
    times=sorted(row['ms'] for row in rows)
    successes=[row['ms'] for row in rows if row['status']==200]
    return {'requests':len(rows),'statuses':dict(Counter(str(r['status']) for r in rows)),
        'median_all_ms':round(statistics.median(times),3),'p95_all_ms':times[min(len(times)-1,int(.95*len(times)))],
        'max_all_ms':max(times),'max_success_ms':max(successes) if successes else None,
        'max_bytes':max(row['bytes'] for row in rows)}


def burst(path):
    global peak
    peak=0;barrier=threading.Barrier(args.connections);start=time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.connections) as pool:
        rows=list(pool.map(lambda _:request(path,barrier),range(args.connections)))
    return dict(summary(rows),peak_active_client_requests=peak,duration_seconds=round(time.perf_counter()-start,3))


normal={path:summary([request(path) for _ in range(5)]) for path in
    ['/portal/','/api/config','/api/categorias?include_contents=false','/api/noticias','/api/eventos','/api/avisos','/api/servicios','/api/encuestas']}
peak=0
with ThreadPoolExecutor(max_workers=args.connections) as pool:
    start=time.perf_counter()
    futures=[]
    for i in range(args.rate*args.seconds):
        due=start+i/args.rate
        futures.append(pool.submit(request,'/api/noticias',None,max(0,due-time.perf_counter())))
    paced=dict(summary([future.result() for future in futures]),rate=args.rate,scheduled_seconds=args.seconds,peak_active_client_requests=peak)
result={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'base':args.base,'tool':'Python http.client + bounded ThreadPoolExecutor/Barrier',
    'environment':{'os':platform.platform(),'processor':platform.processor(),'logical_cpus':os.cpu_count(),'python':platform.python_version(),
        'server':'Waitress 3.0.2, 8 threads, backlog 256, connection_limit 256, 30s channel timeout; Django/PostgreSQL local'},
    'html_bytes':(root/'captive-portal/dist/index.html').stat().st_size,'normal_5_each':normal,'paced_api':paced,
    'burst_html':burst('/portal/'),'burst_api':burst('/api/noticias'),
    'limits':['Only one burst per endpoint; API limiter remains 120/min/IP. 429 responses are expected when its budget is exceeded.',
        'Paced requests do not represent 200 simultaneous active clients. Burst peak is measured separately.',
        'Loopback/one process/one source IP, no TLS or WiFi/radio and no browser rendering; does not certify institutional RNF-01/02/03.']}
target=root/'docs/pruebas/RENDIMIENTO_FINAL.json';target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
