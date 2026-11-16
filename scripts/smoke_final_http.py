"""Complete authorized thesis demo over real local HTTP; never prints credentials.

Creates its own manager/grants/news/survey. Finally soft-deletes only its contents,
deactivates its manager (history retained), and conditionally restores mail preference.
"""
import csv
import http.cookiejar
import io
import json
import os
from pathlib import Path
import secrets
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

root = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'backend')); os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from pypdf import PdfReader
if settings.PRODUCTION or settings.AUTH_PROVIDER!='demo' or settings.EMAIL_MODE not in ('file','console','memory'):
    sys.exit('Solo se permite la comprobación local demo con proveedor de correo sin red.')
base = 'http://127.0.0.1:8010'
credentials = dict(line.split('\t',1) for line in (root/'.local/demo-credentials.txt').read_text(encoding='utf-8').splitlines())


class Browser:
    def __init__(self):
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        self.csrf = ''

    def request(self,path,body=None,method=None,status=200,raw=False):
        headers={'Content-Type':'application/json','Origin':base}
        if self.csrf: headers['X-CSRFToken']=self.csrf
        request=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
        try: response=self.opener.open(request,timeout=30)
        except urllib.error.HTTPError as error: response=error
        with response:
            content=response.read()
            assert response.status==status, f'{method or "GET"} {path}: {response.status}, esperado {status}'
            return content if raw else json.loads(content) if content else None

    def login(self,email,password):
        self.csrf=self.request('/api/csrf/')['csrfToken']
        result=self.request('/auth/login',{'email':email,'password':password})
        self.csrf=self.request('/api/csrf/')['csrfToken']
        return result


checks=[]
def check(condition,label):
    assert condition,label
    checks.append(label);print('OK',label,flush=True)


superadmin,admin,manager,visitor=Browser(),Browser(),Browser(),Browser()
created=[];manager_id=None;mail_timestamp=None;old_mail=None
started=datetime.now(timezone.utc)
try:
    superadmin.login('demo.superadmin@uho.edu.cu',credentials['demo.superadmin@uho.edu.cu'])
    check(superadmin.request('/api/me/')['role_code']=='superadmin','Superadmin inicia sesión')
    meta=superadmin.request('/api/admin/content-metadata/')
    news=next(c for c in meta['categories'] if c['content_type']=='news')
    surveys=next(c for c in meta['categories'] if c['content_type']=='survey')
    roles=superadmin.request('/api/admin/roles/')['results']
    role=next(r['id'] for r in roles if r['code']=='gestor')
    unique=secrets.token_hex(6);email='demo.tesis.'+unique+'@uho.edu.cu';password=secrets.token_urlsafe(24)
    row=superadmin.request('/api/admin/users/',{'email':email,'role':role,'categories':[news['id'],surveys['id']],'password':password},status=201)
    manager_id=row['id']
    check(row['categories']==[news['id'],surveys['id']],'Superadmin crea Gestor y asigna categorías')
    for category in [news,surveys]:
        for operation in ['view','create','edit','delete','submit']:
            superadmin.request('/api/admin/permissions/',{'user':manager_id,'category':category['id'],'operation':operation},status=201)
    check(manager.login(email,password)['role_code']=='gestor','Gestor nuevo inicia sesión con permisos reales')
    manager.request('/api/admin/users/',status=403);manager.request('/api/admin/audit/',status=403)
    check(True,'Gestor no puede administrar usuarios ni consultar auditoría')
    configuration=superadmin.request('/api/admin/settings/')
    old_mail=configuration['email_notifications']
    mail_timestamp=superadmin.request('/api/admin/settings/',{'email_notifications':True},method='PATCH')['updated_at']
    admin.login('demo.admin@uho.edu.cu',credentials['demo.admin@uho.edu.cu'])
    before=admin.request('/api/admin/dashboard/?period=today')['views']
    item=manager.request('/api/admin/contents/',{'category':news['id'],'title':('DEMO tesis B5 '+unique)[:news['title_limit']],
        'description':'Versión inicial DEMO.'[:news['description_limit']], 'validity':'default',
        'details':{'area':meta['areas'][0]['id']},'extra_fields':{k:'DEMO' for k in news['required_fields']}},status=201)
    pk=item['id'];created.append(pk)
    check(datetime.fromisoformat(item['ends_at'])-datetime.fromisoformat(item['starts_at'])==timedelta(days=configuration['default_validity_days']),
        'Vigencia predeterminada aplicada desde configuración')
    check(item['state']=='draft' and not any(x['id']==pk for x in visitor.request('/api/noticias')),'Noticia borrador no es pública')
    manager.request(f'/api/admin/contents/{pk}/submit/',{})
    notifications=admin.request('/api/admin/notifications/?kind=content.submitted')['results']
    notice=next(n for n in notifications if n['resource_id']==pk)
    check(notice['mail_state']=='sent','Admin recibe notificación y correo de demostración local')
    admin.request(f'/api/admin/notifications/{notice["id"]}/mark_read/',{})
    check(admin.request(f'/api/admin/notifications/{notice["id"]}/')['read'],'Lectura de notificación persistida')
    approval=next(a for a in admin.request('/api/admin/approvals/')['results'] if a['content']==pk)
    admin.request(f'/api/admin/approvals/{approval["id"]}/decide/',{'approved':True})
    public=next(x for x in visitor.request('/api/noticias') if x['id']==pk)
    check(public['description']==item['description'],'Noticia aprobada aparece en API consumida por el portal')
    visitor.csrf=visitor.request('/portal-auth/session')['csrfToken']
    private=(root/'.local/portal-demo-credentials.txt').read_text(encoding='utf-8').splitlines()
    username,secret=next(line.split(': ',1) for line in private if line.startswith('demo.estudiante: '))
    state=visitor.request('/portal-auth/session',{'username':username,'password':secret});visitor.csrf=state['csrfToken']
    check(state['authenticated'] and not state['network_access_granted'],'Visitante demo inicia sesión sin conceder Internet')
    visitor.request('/api/vistas',{'section':news['slug'],'content':pk},status=201)
    check(admin.request('/api/admin/dashboard/?period=today')['views']>=before+1,'Vista del visitante incrementa dashboard real')
    changed='Versión revisada DEMO.'[:news['description_limit']]
    revision=manager.request(f'/api/admin/contents/{pk}/',{'description':changed},method='PATCH')
    check(revision['state']=='draft' and next(x for x in visitor.request('/api/noticias') if x['id']==pk)['description']==item['description'],
        'Edición del Gestor conserva versión pública anterior')
    manager.request(f'/api/admin/contents/{pk}/submit/',{})
    approval=next(a for a in admin.request('/api/admin/approvals/')['results'] if a['content']==pk)
    admin.request(f'/api/admin/approvals/{approval["id"]}/decide/',{'approved':True})
    check(next(x for x in visitor.request('/api/noticias') if x['id']==pk)['description']==changed,'Segunda aprobación publica revisión actualizada')
    questions=[{'text':'Una opción DEMO','kind':'single','required':True,'options':[{'text':'A'},{'text':'B'}]},
        {'text':'Varias opciones DEMO','kind':'multiple','required':True,'options':[{'text':'C'},{'text':'D'}]}]
    if meta['survey']['allow_open_questions']:questions.append({'text':'Comentario DEMO','kind':'open','required':False,'options':[]})
    questions=questions[:meta['survey']['max_questions']]
    survey=manager.request('/api/admin/contents/',{'category':surveys['id'],'title':('DEMO encuesta tesis '+unique)[:surveys['title_limit']],
        'description':'Participación de comprobación local.'[:surveys['description_limit']],'validity':'always',
        'details':{'external_url':'','questions':questions},'extra_fields':{k:'DEMO' for k in surveys['required_fields']}},status=201)
    sid=survey['id'];created.append(sid);manager.request(f'/api/admin/contents/{sid}/submit/',{})
    approval=next(a for a in admin.request('/api/admin/approvals/')['results'] if a['content']==sid)
    admin.request(f'/api/admin/approvals/{approval["id"]}/decide/',{'approved':True})
    public=next(x for x in visitor.request('/api/encuestas') if x['id']==sid)
    answers=[{'question':q['id'],'options':[] if q['kind']=='open' else [o['id'] for o in q['options'][:(2 if q['kind']=='multiple' else 1)]],
        'value':'DEMO tesis: respuesta de comprobación' if q['kind']=='open' else ''} for q in public['details']['questions']]
    visitor.request(f'/api/encuestas/{sid}/respuestas',{'answers':answers},status=201)
    result=admin.request(f'/api/admin/contents/{sid}/results/')
    check(result['total']==1 and result['answers_total']==len(questions),'Encuesta respondida y resultados persistidos en PostgreSQL')
    visitor.request(f'/api/encuestas/{sid}/respuestas',{'answers':answers},status=400)
    check(True,'Respuesta duplicada rechazada sin duplicar participación')
    for kind in ['general','accesses','contents','surveys','security','audit']:
        browser=superadmin if kind=='audit' else admin
        for fmt in ['csv','pdf']:
            data=browser.request(f'/api/admin/reports/{kind}/?content={sid}&period=today&file_format={fmt}',raw=True)
            valid=bool(list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))) if fmt=='csv' else len(PdfReader(io.BytesIO(data)).pages)>0
            check(valid,f'Reporte {kind} {fmt} descargado y analizado')
    events=superadmin.request('/api/admin/audit/?search='+str(pk))['results']
    check(any(e['resource']==str(pk) and e['action']=='content.approve' for e in events),'Auditoría contiene aprobación del flujo completo')
    visitor.request('/portal-auth/logout',{})
    check(not visitor.request('/portal-auth/session')['authenticated'],'Logout visitante invalida sesión')
finally:
    for pk in created:superadmin.request(f'/api/admin/contents/{pk}/',method='DELETE',status=204)
    if manager_id:superadmin.request(f'/api/admin/users/{manager_id}/',{'is_active':False,'authorized':False},method='PATCH')
    if mail_timestamp and superadmin.request('/api/admin/settings/')['updated_at']==mail_timestamp:
        superadmin.request('/api/admin/settings/',{'email_notifications':old_mail},method='PATCH')
    for browser in [manager,admin,superadmin]:
        if browser.csrf:
            try: browser.request('/auth/logout',{})
            except AssertionError: pass  # Own manager has already been deactivated.
result={'started_utc':started.isoformat(),'finished_utc':datetime.now(timezone.utc).isoformat(),'base':base,
    'passed':len(checks),'failed':0,'checks':checks,'owned_content_ids':created,'owned_manager_id':manager_id,
    'cleanup':'Own contents soft-deleted, manager deactivated, history/responses retained, mail preference restored if unchanged.',
    'limitations':'Real local HTTP/API + PostgreSQL; does not certify browser rendering or institutional integrations.'}
(root/'docs/pruebas/E2E_FINAL.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Comprobación integral HTTP aprobada. Solo se retiraron lógicamente sus contenidos propios y se desactivó su usuario propio.')
