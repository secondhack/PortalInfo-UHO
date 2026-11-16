"""Local Block 3 smoke checks, with real HTTP, local mail and export parsers.

Only its own content and notification are changed. Demo seed alerts are read.
No SMTP, credentials, cookies or open-answer contents are printed.
"""
import csv
import http.cookiejar
import io
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request
from datetime import datetime,timezone

root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'backend'));os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from pypdf import PdfReader
if settings.PRODUCTION or settings.AUTH_PROVIDER!='demo' or settings.EMAIL_MODE not in ['file','console','memory']:
    raise RuntimeError('This check only runs against a local demo with a non-SMTP mail provider.')
credentials=dict(line.split('\t',1) for line in (root/'.local/demo-credentials.txt').read_text(encoding='utf-8').splitlines())
base='http://127.0.0.1:8010'
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
csrf=None

def request(path,body=None,method=None,binary=False):
    headers={'Content-Type':'application/json'}
    if csrf:headers['X-CSRFToken']=csrf
    req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
    with opener.open(req,timeout=30) as response:
        raw=response.read();result=raw if binary else json.loads(raw) if raw else None
        print(response.status,method or ('POST' if body is not None else 'GET'),path)
        return result

def login(role):
    global csrf
    csrf=request('/api/csrf/')['csrfToken']
    email=f'demo.{role}@uho.edu.cu'
    request('/auth/login',{'email':email,'password':credentials[email]})
    csrf=request('/api/csrf/')['csrfToken']

content_id=None;old_mail=False;activation_timestamp=None
try:
    login('superadmin');before=request('/api/admin/settings/');old_mail=before['email_notifications']
    activation=request('/api/admin/settings/',{'email_notifications':True},method='PATCH');activation_timestamp=activation['updated_at']
    request('/auth/logout',{});login('gestor')
    meta=request('/api/admin/content-metadata/');cat=next(c for c in meta['categories'] if c['content_type']=='news' and 'create' in c['permissions'])
    title='DEMO HTTP B3 '+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    item=request('/api/admin/contents/',{'category':cat['id'],'title':title[:cat['title_limit']],
        'description':'Comprobación local de notificaciones y reportes.'[:cat['description_limit']],
        'validity':'always','details':{'area':meta['areas'][0]['id']}})
    content_id=item['id'];request(f'/api/admin/contents/{content_id}/submit/',{})
    request('/auth/logout',{});login('admin')
    matches=request('/api/admin/approvals/?'+urllib.parse.urlencode({'search':title,'state':'pending'}))['results']
    approval=next(r for r in matches if r['content']==content_id)
    request(f'/api/admin/approvals/{approval["id"]}/decide/',{'approved':True})
    request(f'/api/admin/approvals/{approval["id"]}/decide/',{'approved':True})
    request('/auth/logout',{});login('gestor')
    inbox=request('/api/admin/notifications/?kind=content.approved')['results']
    notice=next(n for n in inbox if n['resource_id']==content_id)
    assert notice['mail_state']=='sent'
    unread=request('/api/admin/notifications/unread/')['count']
    request(f'/api/admin/notifications/{notice["id"]}/mark_read/',{})
    assert request('/api/admin/notifications/unread/')['count']==unread-1
    request('/api/demo/portal-access/',{})
    request('/api/vistas',{'section':cat['slug'],'content':content_id})
    request('/auth/logout',{});login('admin')
    stats=request('/api/admin/estadisticas?period=today');assert stats['accesses']>=1 and stats['views']>=1
    request('/api/admin/logs?period=today');request('/api/admin/dashboard/?period=today')
    request('/api/admin/security-alerts/?data_scope=demo')
    request('/api/admin/security-alerts/scan/?data_scope=demo',{})
    survey=request('/api/encuestas')[0]['id']
    results=request(f'/api/admin/contents/{survey}/results/?data_scope=all');assert results['total']>=2
    for kind in ['general','accesses','contents','surveys','security']:
        query=urllib.parse.urlencode({'period':'7d','data_scope':'all','content':survey})
        rows=list(csv.reader(io.StringIO(request(f'/api/admin/reports/{kind}/?{query}&file_format=csv',binary=True).decode('utf-8-sig'))))
        assert rows
        pdf=request(f'/api/admin/reports/{kind}/?{query}&file_format=pdf',binary=True)
        assert len(PdfReader(io.BytesIO(pdf)).pages)>0
    request('/auth/logout',{});login('superadmin')
    for fmt in ['csv','pdf']:
        data=request('/api/admin/reports/audit/?period=today&file_format='+fmt,binary=True)
        assert data.startswith(b'%PDF-') if fmt=='pdf' else len(data)>0
    request('/api/admin/audit/?period=today&entity=content')
finally:
    login('superadmin')
    if content_id:request(f'/api/admin/contents/{content_id}/',method='DELETE')
    current=request('/api/admin/settings/')
    if activation_timestamp and current['updated_at']==activation_timestamp:
        request('/api/admin/settings/',{'email_notifications':old_mail},method='PATCH')
    request('/auth/logout',{})
print('Block 3 HTTP checks passed; local mail was delivered, exports parsed and only own DEMO content soft-deleted.')
