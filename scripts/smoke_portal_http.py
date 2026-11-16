"""Real loopback integration: independent visitors, survey, views, logout and CMS metrics.

Creates one clearly named DEMO survey and soft-deletes only that survey. No pre-existing
content/settings/users are changed. Credentials/cookies/answer values are never printed.
"""
import http.cookiejar
import json
from pathlib import Path
import urllib.error
import urllib.request
from datetime import datetime, timezone

root = Path(__file__).resolve().parent.parent
base = 'http://127.0.0.1:8010'


class Browser:
    def __init__(self):
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        self.csrf = ''

    def request(self, path, body=None, method=None, expected=200, raw=False):
        headers = {'Content-Type':'application/json', 'Origin':base}
        if self.csrf: headers['X-CSRFToken'] = self.csrf
        request = urllib.request.Request(base+path, data=json.dumps(body).encode() if body is not None else None,
            method=method, headers=headers)
        try: response = self.opener.open(request, timeout=20)
        except urllib.error.HTTPError as error: response = error
        with response:
            data = response.read()
            assert response.status == expected, f'{path}: expected {expected}, received {response.status}'
            print(response.status, method or ('POST' if body is not None else 'GET'), path)
            return data if raw else json.loads(data) if data else None


admin, visitor = Browser(), Browser()
health = admin.request('/api/health/')
assert health['auth_provider'] == 'demo', 'Only run against the local demonstration.'
page = visitor.request('/portal/', raw=True)
assert len(page) <= 204800 and b'id="login-form"' in page
state = visitor.request('/portal-auth/session'); visitor.csrf = state['csrfToken']
assert state['mode'] == 'demo' and not state['authenticated']
private = (root/'.local/portal-demo-credentials.txt').read_text(encoding='utf-8').splitlines()
username, password = next(line.split(': ',1) for line in private if line.startswith('demo.estudiante: '))
state = visitor.request('/portal-auth/session', {'username':username,'password':password})
visitor.csrf = state['csrfToken']
assert state['authenticated'] and not state['network_access_granted'] and state['identity']['photo'] is None
visitor.request('/api/admin/contents/', expected=403)
config = visitor.request('/api/config')
categories = visitor.request('/api/categorias?include_contents=false')
assert len(config['sections']) == len(categories)
for category in categories:
    rows = visitor.request('/api/'+category['slug'])
    assert len(rows) <= category['max_visible']
visitor.request('/api/vistas', {'section':'portal'}, expected=201)

credentials = dict(line.split('\t',1) for line in (root/'.local/demo-credentials.txt').read_text(encoding='utf-8').splitlines())
admin.csrf = admin.request('/api/csrf/')['csrfToken']
email = 'demo.admin@uho.edu.cu'
admin.request('/auth/login', {'email':email,'password':credentials[email]})
admin.csrf = admin.request('/api/csrf/')['csrfToken']
metadata = admin.request('/api/admin/content-metadata/')
category = next(c for c in metadata['categories'] if c['content_type']=='survey')
content_id = None
try:
    item = admin.request('/api/admin/contents/', {'category':category['id'],
        'title':('DEMO HTTP B4 '+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S'))[:category['title_limit']],
        'description':'Encuesta ficticia de comprobación del portal.'[:category['description_limit']],
        'validity':'always','details':{'external_url':'','questions':[
            {'text':'Selecciona una opción DEMO','kind':'single','required':True,'options':[{'text':'A'},{'text':'B'}]},
            {'text':'Selecciona varias DEMO','kind':'multiple','required':True,'options':[{'text':'C'},{'text':'D'}]},
            {'text':'Texto DEMO','kind':'open','required':False,'options':[]}] }}, expected=201)
    content_id = item['id']
    admin.request(f'/api/admin/contents/{content_id}/submit/', {})
    admin.request(f'/api/admin/contents/{content_id}/review/', {'approved':True})
    survey = next(row for row in visitor.request('/api/encuestas') if row['id']==content_id)
    answers = [{'question':q['id'], 'options':[] if q['kind']=='open' else [o['id'] for o in q['options'][:(2 if q['kind']=='multiple' else 1)]],
        'value':'DEMO comprobación HTTP B4' if q['kind']=='open' else ''} for q in survey['details']['questions']]
    visitor.request(f'/api/encuestas/{content_id}/respuestas', {'answers':answers}, expected=201)
    visitor.request(f'/api/encuestas/{content_id}/respuestas', {'answers':answers}, expected=400)
    visitor.request('/api/vistas', {'section':'encuestas','content':content_id}, expected=201)
    results = admin.request(f'/api/admin/contents/{content_id}/results/')
    assert results['total']==1 and results['answers_total']>=2
    stats = admin.request('/api/admin/estadisticas?period=today')
    assert any(row['user_type']=='demo_estudiantes' for row in stats['by_user_type'])
    old_cookie = next(c.value for c in visitor.cookies if c.name=='sessionid')
    visitor.request('/portal-auth/logout', {})
    assert not visitor.request('/portal-auth/session')['authenticated']
    replay = urllib.request.Request(base+'/portal-auth/session', headers={'Cookie':'sessionid='+old_cookie})
    with urllib.request.urlopen(replay, timeout=20) as response:
        assert not json.load(response)['authenticated']
finally:
    if content_id: admin.request(f'/api/admin/contents/{content_id}/', method='DELETE', expected=204)
    admin.request('/auth/logout', {})
print('Portal HTTP checks passed. Only own DEMO survey soft-deleted; history and test participation retained.')
