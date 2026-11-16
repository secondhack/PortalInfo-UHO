"""Exercise the real local CMS over HTTP; create DEMO checks and soft-delete them.

No credentials or cookies are printed. Existing content is never edited.
"""
import http.cookiejar
import json
from pathlib import Path
import urllib.request

root=Path(__file__).resolve().parent.parent
credentials=(root/'.local/demo-credentials.txt').read_text(encoding='utf-8').splitlines()
email,password=next(line.split('\t',1) for line in credentials if line.startswith('demo.admin@'))
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
base='http://127.0.0.1:8010'
csrf=None

def request(path,body=None,method=None):
    headers={'Content-Type':'application/json'}
    if csrf:headers['X-CSRFToken']=csrf
    req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
    with opener.open(req,timeout=20) as response:
        result=json.load(response) if response.status!=204 else None
        print(response.status,method or ('POST' if body is not None else 'GET'),path)
        return result

csrf=request('/api/csrf/')['csrfToken']
request('/auth/login',{'email':email,'password':password})
csrf=request('/api/csrf/')['csrfToken']
metadata=request('/api/admin/content-metadata/')
created=[]
try:
    for category in metadata['categories']:
        kind=category['content_type'];details={}
        if kind in ('news','event','service'): details['area']=metadata['areas'][0]['id']
        if kind=='event':details.update(event_at='2027-01-15T15:00:00Z',contact='Contacto ficticio de comprobación DEMO')
        if kind=='service':details['access_url']='https://example.invalid/comprobacion'
        if kind=='survey':details={'external_url':'','questions':[{'text':'Pregunta DEMO de comprobación','kind':'single','required':True,'options':[{'text':'Sí'},{'text':'No'}]}]}
        body={'category':category['id'],'title':'DEMO · comprobación HTTP'[:category['title_limit']],
            'description':'Contenido ficticio creado exclusivamente para comprobar el CMS.'[:category['description_limit']],
            'validity':'always','details':details,'extra_fields':{key:'DEMO' for key in category['required_fields']}}
        item=request('/api/admin/contents/',body);pk=item['id'];created.append(pk)
        request(f'/api/admin/contents/{pk}/submit/',{})
        request(f'/api/admin/contents/{pk}/review/',{'approved':True})
        public=request('/api/'+category['slug']);published=next(row for row in public if row['id']==pk)
        if kind=='survey':
            q=published['details']['questions'][0]
            request(f'/api/encuestas/{pk}/respuestas',{'answers':[{'question':q['id'],'options':[q['options'][0]['id']]}]})
            assert request(f'/api/admin/contents/{pk}/results/')['total']==1
        request(f'/api/admin/contents/{pk}/',{'title':'DEMO · corregido'[:category['title_limit']]},method='PATCH')
        request(f'/api/admin/contents/{pk}/visibility/',{'manual_active':False})
        assert pk not in [row['id'] for row in request('/api/'+category['slug'])]
        request(f'/api/admin/contents/{pk}/history/')
    request('/api/categorias')
    request('/api/config')
finally:
    for pk in created:request(f'/api/admin/contents/{pk}/',method='DELETE')
    request('/auth/logout',{})
print('CMS HTTP checks passed. Created DEMO checks were soft-deleted; prior data was preserved.')
