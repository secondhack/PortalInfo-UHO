"""Local HTTP smoke check; keeps demo credentials and cookies out of output."""
import http.cookiejar
import json
from pathlib import Path
import urllib.request

root=Path(__file__).resolve().parent.parent
credentials=(root/'.local/demo-credentials.txt').read_text(encoding='utf-8').splitlines()
email,password=next(line.split('\t',1) for line in credentials if line.startswith('demo.superadmin@'))
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
base='http://127.0.0.1:8010'

def request(path, body=None, csrf=None):
    headers={'Content-Type':'application/json'}
    if csrf: headers['X-CSRFToken']=csrf
    req=urllib.request.Request(base+path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    with opener.open(req,timeout=15) as response:
        data=json.load(response)
        print(response.status,path)
        return data

request('/api/health/')
csrf=request('/api/csrf/')['csrfToken']
me=request('/auth/login',{'email':email,'password':password},csrf)
assert me['role_code']=='superadmin' and me['demo']
for path in ['/api/me/','/api/admin/users/','/api/admin/roles/','/api/admin/permissions/','/api/admin/categories/','/api/admin/catalog-types/','/api/admin/catalog-items/','/api/admin/settings/','/api/admin/dashboard/','/api/admin/audit/','/api/config']:
    request(path)
csrf=request('/api/csrf/')['csrfToken']
request('/auth/logout',{},csrf)
with urllib.request.urlopen('http://127.0.0.1:5174',timeout=15) as response:
    assert response.status==200
    assert b'PortalInfo UHO' in response.read()
    print(200,'React /')
print('HTTP smoke passed; credentials/cookies were not printed.')
