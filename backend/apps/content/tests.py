from datetime import datetime,timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError,transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import Role,Grant
from apps.approvals.models import Approval
from apps.audit.models import AuditEvent
from apps.catalogs.models import Category,CatalogType,CatalogItem
from apps.notifications.models import Notification
from apps.settings_app.models import GlobalSettings
from .models import Content,Question,Response,Submission,Publication
from .queries import visible_publications
from .services import register_expirations
from .validation import validity_dates


class ContentTests(TestCase):
    def test_configured_default_validity_is_applied_and_preserved(self):
        cfg=GlobalSettings.current();cfg.default_validity_days=8;cfg.save()
        data=self.payload('avisos');data.pop('validity')
        result=self.client.post('/api/admin/contents/',data,format='json')
        self.assertEqual(result.status_code,201,result.data)
        item=Content.objects.get(pk=result.data['id'])
        self.assertEqual(item.validity,'custom')
        self.assertEqual(item.ends_at-item.starts_at,timedelta(days=8))
        previous=item.ends_at
        updated=self.client.patch(f'/api/admin/contents/{item.pk}/',{'title':'Texto corregido'},format='json')
        self.assertEqual(updated.status_code,200,updated.data)
        item.refresh_from_db();self.assertEqual(item.ends_at,previous)

    def test_explicit_three_days_is_independent_of_default(self):
        cfg=GlobalSettings.current();cfg.default_validity_days=8;cfg.save()
        pk=self.create('avisos',validity='three_days')
        item=Content.objects.get(pk=pk)
        self.assertEqual(item.ends_at-item.starts_at,timedelta(days=3))

    @classmethod
    def setUpTestData(cls):
        cls.users={}
        for code in ['superadmin','admin','gestor']:
            role=Role.objects.create(code=code,name=code)
            cls.users[code]=get_user_model().objects.create_user(username=code,email=code+'@uho.edu.cu',password='Test-secret-182!',role=role,demo=True)
        cls.categories={}
        for slug,kind in [('noticias','news'),('eventos','event'),('avisos','notice'),('servicios','service'),('encuestas','survey'),('logros','generic')]:
            cls.categories[slug]=Category.objects.create(name=slug,slug=slug,content_type=kind,dynamic=kind=='generic',max_visible=2)
        cls.users['gestor'].categories.add(cls.categories['noticias'],cls.categories['encuestas'])
        for category in [cls.categories['noticias'],cls.categories['encuestas']]:
            for operation in ['view','create','edit','delete','submit']:
                Grant.objects.create(role=cls.users['gestor'].role,category=category,operation=operation)
        catalog=CatalogType.objects.create(name='Áreas',slug='areas')
        cls.area=CatalogItem.objects.create(catalog=catalog,name='Área DEMO')
        GlobalSettings.current()

    def setUp(self):
        self.client=APIClient();self.client.force_login(self.users['admin'])
        from django.core.cache import cache
        cache.clear()

    def payload(self,slug='noticias',**changes):
        details={}
        if slug=='noticias':details={'area':self.area.pk,'external_url':'https://example.invalid/noticia'}
        if slug=='eventos':details={'area':self.area.pk,'event_at':(timezone.now()+timedelta(days=4)).isoformat(),'contact':'Contacto DEMO'}
        if slug=='servicios':details={'area':self.area.pk,'access_url':'https://example.invalid/servicio'}
        if slug=='encuestas':details={'external_url':'','questions':[
            {'text':'Simple','kind':'single','required':True,'options':[{'text':'A'},{'text':'B'}]},
            {'text':'Múltiple','kind':'multiple','required':True,'options':[{'text':'C'},{'text':'D'}]},
            {'text':'Abierta','kind':'open','required':False,'options':[]}]}
        value={'category':self.categories[slug].pk,'title':'Título DEMO','description':'Descripción de ejemplo.','validity':'always','details':details}
        value.update(changes);return value

    def create(self,slug='noticias',**changes):
        response=self.client.post('/api/admin/contents/',self.payload(slug,**changes),format='json')
        self.assertEqual(response.status_code,201,response.data)
        return response.data['id']

    def send(self,pk):
        response=self.client.post(f'/api/admin/contents/{pk}/submit/',{},format='json')
        self.assertEqual(response.status_code,200,response.data);return response

    def approve(self,pk):
        self.send(pk)
        response=self.client.post(f'/api/admin/contents/{pk}/review/',{'approved':True},format='json')
        self.assertEqual(response.status_code,200,response.data)

    def survey(self):
        pk=self.create('encuestas');self.approve(pk)
        definition=APIClient().get('/api/encuestas').data[0]['details']['questions']
        return pk,definition

    def vote(self,client,pk,questions,**kwargs):
        answers=[]
        for q in questions:
            if q['kind']=='open':answers.append({'question':q['id'],'value':'Respuesta real de prueba'})
            else:answers.append({'question':q['id'],'options':[o['id'] for o in q['options']][:1 if q['kind']=='single' else 2]})
        return client.post(f'/api/encuestas/{pk}/respuestas',{'answers':answers},format='json',**kwargs)

    def test_crud_all_six_types(self):
        for slug in self.categories:
            with self.subTest(slug=slug):
                pk=self.create(slug)
                self.assertEqual(self.client.get(f'/api/admin/contents/{pk}/').status_code,200)
                response=self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Título editado'},format='json')
                self.assertEqual(response.status_code,200,response.data)
                self.assertEqual(self.client.get('/api/admin/contents/',{'category':self.categories[slug].pk,'search':'editado'}).data['count'],1)
                self.assertEqual(self.client.delete(f'/api/admin/contents/{pk}/').status_code,204)
                self.assertIsNotNone(Content.objects.get(pk=pk).deleted_at)
                self.assertEqual(self.client.get(f'/api/admin/contents/{pk}/').status_code,404)

    def test_admin_search_filters_dates_order_and_pagination(self):
        for n in range(21):self.create('eventos',title=f'Evento {n:02d}')
        response=self.client.get('/api/admin/contents/',{'category':self.categories['eventos'].pk,'area':self.area.pk,'state':'draft','ordering':'title','date_from':(timezone.now()-timedelta(days=1)).isoformat()})
        self.assertEqual(response.data['count'],21);self.assertEqual(len(response.data['results']),20)
        self.assertTrue(response.data['next']);self.assertEqual(response.data['results'][0]['title'],'Evento 00')
        self.assertEqual(len(self.client.get('/api/admin/contents/?page=2').data['results']),1)
        self.assertEqual(self.client.get('/api/admin/contents/',{'area':99999}).data['count'],0)
        self.assertEqual(self.client.get('/api/admin/contents/',{'event_from':(timezone.now()+timedelta(days=10)).isoformat()}).data['count'],0)

    def test_permissions_categories_and_unauthenticated(self):
        pk=self.create('avisos')
        self.assertEqual(APIClient().get('/api/admin/contents/').status_code,403)
        self.client.force_login(self.users['gestor'])
        self.assertEqual(self.client.get(f'/api/admin/contents/{pk}/').status_code,404)
        self.assertEqual(self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Intrusión'}).status_code,404)
        self.assertEqual(self.client.post('/api/admin/contents/',self.payload('avisos'),format='json').status_code,403)
        own=self.create()
        self.assertEqual(self.client.post(f'/api/admin/contents/{own}/review/',{'approved':True},format='json').status_code,403)
        Grant.objects.filter(role=self.users['gestor'].role,operation='edit').delete()
        self.assertEqual(self.client.patch(f'/api/admin/contents/{own}/',{'title':'Sin permiso'}).status_code,403)

    def test_superadmin_and_manager_operation_grants(self):
        self.client.force_login(self.users['superadmin']);self.create('logros')
        self.client.force_login(self.users['gestor']);pk=self.create()
        Grant.objects.filter(role=self.users['gestor'].role,operation='delete').delete()
        self.assertEqual(self.client.delete(f'/api/admin/contents/{pk}/').status_code,403)
        Grant.objects.filter(role=self.users['gestor'].role,operation='submit').delete()
        self.assertEqual(self.client.post(f'/api/admin/contents/{pk}/submit/',{},format='json').status_code,403)

    def test_manager_revision_does_not_overwrite_approved_publication(self):
        self.client.force_login(self.users['gestor']);pk=self.create();self.send(pk)
        self.assertEqual(APIClient().get('/api/noticias').data,[])
        self.client.force_login(self.users['admin'])
        self.assertEqual(self.client.post(f'/api/admin/contents/{pk}/review/',{'approved':True},format='json').status_code,200)
        self.client.force_login(self.users['gestor'])
        self.assertEqual(self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Nueva revisión'},format='json').status_code,200)
        self.send(pk)
        self.assertEqual(APIClient().get('/api/noticias').data[0]['title'],'Título DEMO')
        self.client.force_login(self.users['admin'])
        self.client.post(f'/api/admin/contents/{pk}/review/',{'approved':True},format='json')
        self.assertEqual(APIClient().get('/api/noticias').data[0]['title'],'Nueva revisión')
        self.assertEqual(Publication.objects.filter(content_id=pk).count(),2)

    def test_admin_direct_edit_and_rejection_history(self):
        pk=self.create();self.approve(pk)
        response=self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Corrección menor'},format='json')
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(APIClient().get('/api/noticias').data[0]['title'],'Corrección menor')
        self.client.force_login(self.users['gestor']);self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Rechazable'});self.send(pk)
        self.client.force_login(self.users['admin'])
        self.assertEqual(self.client.post(f'/api/admin/contents/{pk}/review/',{'approved':False},format='json').status_code,400)
        self.assertEqual(self.client.post(f'/api/admin/contents/{pk}/review/',{'approved':False,'reason':'Revisar redacción.'},format='json').status_code,200)
        self.assertEqual(APIClient().get('/api/noticias').data[0]['title'],'Corrección menor')
        self.assertEqual(self.client.get(f'/api/admin/contents/{pk}/history/').data['approvals'][0]['reason'],'Revisar redacción.')

    def test_unapproved_visibility_switch_never_publishes(self):
        pk=self.create();self.send(pk)
        for value in [False,True]:
            self.assertEqual(self.client.post(f'/api/admin/contents/{pk}/visibility/',{'manual_active':value},format='json').status_code,200)
            self.assertEqual(APIClient().get('/api/noticias').data,[])

    def test_visibility_switch_approved_and_section_disabled(self):
        pk=self.create();self.approve(pk)
        self.client.post(f'/api/admin/contents/{pk}/visibility/',{'manual_active':False},format='json')
        self.assertEqual(APIClient().get('/api/noticias').data,[])
        self.client.post(f'/api/admin/contents/{pk}/visibility/',{'manual_active':True},format='json')
        self.assertEqual(len(APIClient().get('/api/noticias').data),1)
        for field in ['visible','active']:
            category=self.categories['noticias'];setattr(category,field,False);category.save()
            self.assertEqual(APIClient().get('/api/noticias').data,[])
            setattr(category,field,True);category.save()

    def test_effective_limit_and_warning_without_block(self):
        category=self.categories['noticias'];category.max_visible=1;category.save()
        first=self.create();self.approve(first)
        self.client.force_login(self.users['gestor']);second=self.create(title='Más reciente')
        response=self.send(second);self.assertTrue(response.data['warning'])
        self.client.force_login(self.users['admin']);self.client.post(f'/api/admin/contents/{second}/review/',{'approved':True},format='json')
        public=APIClient().get('/api/noticias').data
        self.assertEqual([row['id'] for row in public],[second])
        self.assertFalse(Content.objects.get(pk=first).effectively_visible)
        self.assertTrue(Content.objects.get(pk=second).effectively_visible)
        self.assertEqual(self.client.get('/api/admin/contents/?visibility=active').data['count'],1)

    def test_temporal_conditions_and_idempotent_expiration(self):
        now=timezone.now()
        pk=self.create(validity='custom',starts_at=(now-timedelta(days=3)).isoformat(),ends_at=(now-timedelta(days=1)).isoformat());self.approve(pk)
        self.assertEqual(APIClient().get('/api/noticias').data,[])
        self.assertEqual(register_expirations(),1);self.assertEqual(register_expirations(),0)
        self.assertEqual(Notification.objects.filter(kind='content.expired').count(),1)
        self.assertEqual(AuditEvent.objects.filter(action='content.expired').count(),1)
        future=self.create(validity='custom',starts_at=(now+timedelta(days=1)).isoformat(),ends_at=(now+timedelta(days=2)).isoformat());self.approve(future)
        self.assertEqual(APIClient().get('/api/noticias').data,[])
        permanent=self.create(validity='always');self.approve(permanent)
        self.assertEqual([p['id'] for p in APIClient().get('/api/noticias').data],[permanent])

    def test_calendar_period_boundaries_and_invalid_ranges(self):
        now=timezone.make_aware(datetime(2026,11,14,12,0))
        expected={'today':(2026,11,15),'week':(2026,11,16),'month':(2026,12,1)}
        for kind,day in expected.items():
            start,end=validity_dates(kind,now=now)
            self.assertEqual(start,now);self.assertEqual((end.year,end.month,end.day),day);self.assertEqual(end.hour,0)
        self.assertEqual(validity_dates('three_days',now=now),(now,now+timedelta(days=3)))
        self.assertEqual(validity_dates('always',now=now),(now,None))
        self.assertEqual(self.client.post('/api/admin/contents/',self.payload(validity='custom'),format='json').status_code,400)
        self.assertEqual(self.client.post('/api/admin/contents/',self.payload(validity='custom',starts_at=now.isoformat(),ends_at=(now-timedelta(hours=1)).isoformat()),format='json').status_code,400)

    def test_character_limits_and_required_dynamic_fields(self):
        category=self.categories['noticias'];category.title_limit=5;category.description_limit=10;category.save()
        self.assertEqual(self.client.post('/api/admin/contents/',self.payload(),format='json').status_code,400)
        self.create(title='Corto',description='Breve')
        dynamic=self.categories['logros'];dynamic.required_fields=['Reconocimiento'];dynamic.save()
        self.assertEqual(self.client.post('/api/admin/contents/',self.payload('logros'),format='json').status_code,400)
        pk=self.create('logros',extra_fields={'Reconocimiento':'Ejemplo'});self.approve(pk)
        self.assertEqual(APIClient().get('/api/logros').data[0]['extra_fields']['Reconocimiento'],'Ejemplo')
        self.assertIn('logros',[r['slug'] for r in APIClient().get('/api/categorias').data])

    def test_dynamic_category_creation_discovery_and_assignment(self):
        self.client.force_login(self.users['superadmin'])
        response=self.client.post('/api/admin/categories/',{'name':'Nueva categoría','slug':'nueva'},format='json')
        self.assertEqual(response.status_code,201)
        cat=Category.objects.get(pk=response.data['id']);self.users['gestor'].categories.add(cat)
        for op in ['view','create','edit','submit']:Grant.objects.create(user=self.users['gestor'],category=cat,operation=op)
        self.client.force_login(self.users['gestor'])
        self.assertIn(cat.pk,[c['id'] for c in self.client.get('/api/admin/content-metadata/').data['categories']])
        response=self.client.post('/api/admin/contents/',{'category':cat.pk,'title':'Logro','description':'Prueba','validity':'always'},format='json')
        self.assertEqual(response.status_code,201,response.data)
        self.send(response.data['id'])

    def test_urls_and_area_validation(self):
        for url in ['javascript:alert(1)','data:text/html,x','ftp://example.invalid','https://user:password@example.invalid']:
            value=self.payload('servicios');value['details']['access_url']=url
            self.assertEqual(self.client.post('/api/admin/contents/',value,format='json').status_code,400)
        value=self.payload();value['details']['area']=99999
        self.assertEqual(self.client.post('/api/admin/contents/',value,format='json').status_code,400)

    def test_public_payload_never_leaks_private_fields_or_drafts(self):
        for slug in self.categories:
            self.create(slug,title='Borrador privado')
            pk=self.create(slug,title='Público');self.approve(pk)
            response=APIClient().get('/api/'+slug)
            self.assertEqual(len(response.data),1)
            payload=str(response.data)
            for secret in ['author','password','approved_by','respondent_key','rejected','Borrador privado']:
                self.assertNotIn(secret,payload)

    def test_survey_limits_and_external_forms(self):
        cfg=GlobalSettings.current();cfg.max_questions=1;cfg.save()
        self.assertEqual(self.client.post('/api/admin/contents/',self.payload('encuestas'),format='json').status_code,400)
        cfg.max_questions=10;cfg.max_options=2;cfg.allow_open_questions=False;cfg.save()
        value=self.payload('encuestas');value['details']['questions']=value['details']['questions'][:1]
        value['details']['questions'][0]['options'].append({'text':'C'})
        self.assertEqual(self.client.post('/api/admin/contents/',value,format='json').status_code,400)
        value=self.payload('encuestas')
        self.assertEqual(self.client.post('/api/admin/contents/',value,format='json').status_code,400)
        value['details']={'external_url':'https://example.invalid/encuesta','questions':[]}
        pk=self.client.post('/api/admin/contents/',value,format='json').data['id'];self.approve(pk)
        self.assertEqual(APIClient().post(f'/api/encuestas/{pk}/respuestas',{'answers':[]},format='json').status_code,400)

    def test_real_survey_answers_results_and_duplicates(self):
        pk,questions=self.survey();client=APIClient()
        self.assertEqual(self.vote(client,pk,questions).status_code,201)
        self.assertEqual(Response.objects.count(),3);self.assertEqual(Submission.objects.count(),1)
        self.assertEqual(self.vote(client,pk,questions).status_code,400)
        result=self.client.get(f'/api/admin/contents/{pk}/results/').data
        self.assertEqual(result['total'],1)
        self.assertEqual(result['versions'][0]['questions'][0]['options'][0]['percentage'],100)
        self.assertEqual(result['versions'][0]['questions'][2]['open_answers'],['Respuesta real de prueba'])
        self.client.force_login(self.users['gestor'])
        self.assertEqual(self.client.get(f'/api/admin/contents/{pk}/results/').status_code,403)

    def test_answers_reject_foreign_options_multiple_single_and_missing_required(self):
        pk,questions=self.survey();client=APIClient()
        cases=[{'answers':[]},{'answers':[{'question':questions[0]['id'],'options':[o['id'] for o in questions[0]['options']]}]},
            {'answers':[{'question':questions[0]['id'],'options':[questions[1]['options'][0]['id']]}]},
            {'answers':[{'question':999999,'value':'Intrusión'}]},
            {'answers':[{'question':questions[0]['id'],'options':[questions[0]['options'][0]['id']] }]*2}]
        for body in cases:self.assertEqual(client.post(f'/api/encuestas/{pk}/respuestas',body,format='json').status_code,400)
        self.assertEqual(Submission.objects.count(),0)

    def test_inactive_survey_and_cross_survey_ids(self):
        first,questions=self.survey();second,_=self.survey()
        self.assertEqual(self.vote(APIClient(),second,questions).status_code,400)
        self.client.post(f'/api/admin/contents/{first}/visibility/',{'manual_active':False},format='json')
        self.assertEqual(self.vote(APIClient(),first,questions).status_code,404)

    def test_survey_revision_preserves_answers_and_public_definition(self):
        pk,questions=self.survey();self.vote(APIClient(),pk,questions)
        self.client.force_login(self.users['gestor'])
        value=self.payload('encuestas');value['details']['questions'][0]['text']='Pregunta nueva'
        response=self.client.patch(f'/api/admin/contents/{pk}/',{'details':value['details']},format='json')
        self.assertEqual(response.status_code,200,response.data)
        self.assertTrue(Question.objects.filter(pk=questions[0]['id'],archived=True).exists())
        self.assertEqual(APIClient().get('/api/encuestas').data[0]['details']['questions'][0]['id'],questions[0]['id'])
        self.assertEqual(self.vote(APIClient(),pk,questions).status_code,201)
        self.assertEqual(Response.objects.count(),6)
        self.assertEqual(self.client.delete(f'/api/admin/contents/{pk}/').status_code,204)
        self.assertEqual(Response.objects.count(),6)
        self.assertEqual(APIClient().get('/api/encuestas').data,[])

    def test_authenticated_voting_and_csrf(self):
        pk,questions=self.survey();cfg=GlobalSettings.current();cfg.vote_requires_auth=True;cfg.save()
        self.assertEqual(self.vote(APIClient(),pk,questions).status_code,403)
        client=APIClient(enforce_csrf_checks=True);client.force_login(self.users['gestor'])
        self.assertEqual(self.vote(client,pk,questions).status_code,403)
        token=client.get('/api/csrf/').data['csrfToken']
        self.assertEqual(self.vote(client,pk,questions,HTTP_X_CSRFTOKEN=token).status_code,201)
        self.assertEqual(self.vote(client,pk,questions,HTTP_X_CSRFTOKEN=token).status_code,400)

    def test_anonymous_vote_requires_csrf_and_is_rate_limited(self):
        pk,questions=self.survey();client=APIClient(enforce_csrf_checks=True)
        self.assertEqual(self.vote(client,pk,questions).status_code,403)
        token=client.get('/api/csrf/').data['csrfToken']
        self.assertEqual(self.vote(client,pk,questions,HTTP_X_CSRFTOKEN=token).status_code,201)
        statuses=[self.vote(client,pk,questions,HTTP_X_CSRFTOKEN=token).status_code for _ in range(11)]
        self.assertIn(429,statuses)

    def test_stale_approvals_invalidated_after_edit(self):
        pk=self.create();self.send(pk)
        self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Cambiado'},format='json')
        self.assertEqual(self.client.post(f'/api/admin/contents/{pk}/review/',{'approved':True},format='json').status_code,400)
        self.assertFalse(Approval.objects.filter(content_id=pk,state='pending').exists())
        self.assertEqual(APIClient().get('/api/noticias').data,[])

    def test_reserved_fields_cannot_publish_and_audit_tracks_actions(self):
        value=self.payload(state='approved')
        self.assertEqual(self.client.post('/api/admin/contents/',value,format='json').status_code,400)
        pk=self.create();self.approve(pk)
        self.client.post(f'/api/admin/contents/{pk}/visibility/',{'manual_active':False},format='json');self.client.delete(f'/api/admin/contents/{pk}/')
        for action in ['content.create','content.submit','content.approve','content.visibility','content.delete']:
            self.assertTrue(AuditEvent.objects.filter(action=action,resource=str(pk)).exists())

    def test_metadata_does_not_expose_security_settings(self):
        self.client.force_login(self.users['gestor']);data=self.client.get('/api/admin/content-metadata/').data
        self.assertEqual(len(data['categories']),2)
        self.assertNotIn('login_attempts',str(data));self.assertNotIn('session_seconds',str(data))

    def test_published_limit_applies_to_survey_responses(self):
        category=self.categories['encuestas'];category.max_visible=1;category.save()
        first,questions=self.survey();self.survey()
        self.assertEqual(self.vote(APIClient(),first,questions).status_code,404)

    def test_submission_database_uniqueness(self):
        pk,questions=self.survey();self.vote(APIClient(),pk,questions)
        original=Submission.objects.first()
        with self.assertRaises(IntegrityError),transaction.atomic():
            Submission.objects.create(publication=original.publication,respondent_key=original.respondent_key)

    def test_seed_is_idempotent_and_does_not_overwrite_manual_content(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from io import StringIO
        from django.conf import settings
        from django.test import override_settings
        pk=self.create(title='Entrada manual que debe conservarse')
        with TemporaryDirectory(dir=settings.BASE_DIR.parent/'.local') as temporary:
            with override_settings(BASE_DIR=Path(temporary)/'backend'):
                call_command('seed_demo',stdout=StringIO())
                ids=list(Content.objects.order_by('pk').values_list('pk',flat=True))
                hashes=list(get_user_model().objects.order_by('pk').values_list('password',flat=True))
                call_command('seed_demo',stdout=StringIO())
                self.assertEqual(ids,list(Content.objects.order_by('pk').values_list('pk',flat=True)))
                self.assertEqual(hashes,list(get_user_model().objects.order_by('pk').values_list('password',flat=True)))
        self.assertEqual(Content.objects.get(pk=pk).title,'Entrada manual que debe conservarse')
        self.assertEqual(Submission.objects.count(),0)

    def test_public_queries_do_not_grow_per_content(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        category=self.categories['avisos'];category.max_visible=10;category.save()
        for n in range(5):
            pk=self.create('avisos',title=f'Aviso {n}');self.approve(pk)
        with CaptureQueriesContext(connection) as queries:
            response=APIClient().get('/api/avisos')
        self.assertEqual(len(response.data),5)
        self.assertLessEqual(len(queries),3)

    def test_forwarded_ip_header_cannot_bypass_vote_throttle(self):
        pk,questions=self.survey();client=APIClient()
        statuses=[self.vote(client,pk,questions,HTTP_X_FORWARDED_FOR=f'192.0.2.{i}').status_code for i in range(12)]
        self.assertIn(429,statuses)

    def test_delete_preserves_publications_and_removes_public_output(self):
        pk=self.create();self.approve(pk)
        self.assertEqual(self.client.delete(f'/api/admin/contents/{pk}/').status_code,204)
        self.assertEqual(Publication.objects.filter(content_id=pk).count(),1)
        self.assertEqual(APIClient().get('/api/noticias').data,[])

    def test_edit_does_not_extend_unchanged_validity(self):
        pk=self.create(validity='today');before=Content.objects.get(pk=pk)
        self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Corrección'},format='json')
        after=Content.objects.get(pk=pk)
        self.assertEqual(before.starts_at,after.starts_at);self.assertEqual(before.ends_at,after.ends_at)

    def test_category_rename_is_reflected_in_public_payload(self):
        pk=self.create('logros');self.approve(pk)
        category=self.categories['logros'];category.slug='logros-nuevos';category.save()
        self.assertEqual(APIClient().get('/api/logros-nuevos').data[0]['category_slug'],'logros-nuevos')
        self.assertEqual(APIClient().get('/api/logros').status_code,404)

    def test_dynamic_slugs_cannot_shadow_system_routes(self):
        self.client.force_login(self.users['superadmin'])
        for slug in ['config','admin','categorias','docs']:
            response=self.client.post('/api/admin/categories/',{'name':'Reservada '+slug,'slug':slug},format='json')
            self.assertEqual(response.status_code,400,response.data)

    def test_builtin_routes_are_stable_and_named_in_openapi(self):
        self.client.force_login(self.users['superadmin'])
        pk=self.categories['noticias'].pk
        self.assertEqual(self.client.patch(f'/api/admin/categories/{pk}/',{'slug':'renombrada'},format='json').status_code,400)
        from drf_spectacular.generators import SchemaGenerator
        paths=SchemaGenerator().get_schema(public=True)['paths']
        for slug in ['noticias','eventos','avisos','servicios','encuestas']:
            self.assertIn('/api/'+slug,paths)
            self.assertEqual(paths['/api/'+slug]['get']['responses']['200']['content']['application/json']['schema']['type'],'array')


class FreshSeedTests(TestCase):
    def test_empty_database_seed_creates_specialized_content_and_preserves_second_run(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from io import StringIO
        from django.conf import settings
        from django.test import override_settings
        from .models import News,Event,Service,Survey
        with TemporaryDirectory(dir=settings.BASE_DIR.parent/'.local') as temporary:
            with override_settings(BASE_DIR=Path(temporary)/'backend'):
                call_command('seed_demo',stdout=StringIO())
                self.assertEqual(Category.objects.get(slug='noticias').content_type,'news')
                for model in [News,Event,Service,Survey]:self.assertEqual(model.objects.count(),7)
                self.assertGreater(Question.objects.count(),0)
                self.assertEqual(Content.objects.count(),42)
                call_command('seed_demo',stdout=StringIO())
                self.assertEqual(Content.objects.count(),42)
                self.assertEqual(Submission.objects.count(),0)
