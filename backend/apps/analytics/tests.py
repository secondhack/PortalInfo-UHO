import csv
import io
from datetime import datetime,timedelta,timezone as dt_timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command,CommandError
from django.db import close_old_connections, connections
from django.test import TestCase,TransactionTestCase,override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User,Role,Grant
from apps.approvals.models import Approval
from apps.audit.models import AuditEvent
from apps.catalogs.models import Category
from apps.content.models import Content,Publication,Submission
from apps.content.services import register_expirations
from apps.notifications.models import Notification,MailDelivery
from apps.notifications.services import send_delivery
from apps.settings_app.models import GlobalSettings
from .models import AccessLog,ContentView,SecurityAlert
from .periods import period_from
from .reports import safe_csv
from .security import detect_alerts


class AdministrationTests(TestCase):
    def test_custom_period_rejects_overflow_instead_of_server_error(self):
        self.client.force_login(self.users['admin'])
        response=self.client.get('/api/admin/estadisticas?period=custom&date_from=9999-01-01&date_to=9999-12-31')
        self.assertEqual(response.status_code,400)

    @classmethod
    def setUpTestData(cls):
        cls.users={}
        for code in ['superadmin','admin','gestor']:
            role=Role.objects.create(code=code,name=code)
            cls.users[code]=User.objects.create_user(username=code,email=code+'@uho.edu.cu',role=role,demo=True)
        cls.category=Category.objects.create(name='Avisos',slug='avisos',content_type='notice',dynamic=False,max_visible=10)
        cls.survey_category=Category.objects.create(name='Encuestas',slug='encuestas',content_type='survey',dynamic=False,max_visible=10)
        cls.users['gestor'].categories.add(cls.category,cls.survey_category)
        for c in [cls.category,cls.survey_category]:
            for op in ['view','create','edit','delete','submit']:Grant.objects.create(role=cls.users['gestor'].role,category=c,operation=op)
        GlobalSettings.current()

    def setUp(self):
        cache.clear();self.client=APIClient();self.client.force_login(self.users['gestor'])

    def create(self,**changes):
        data={'category':self.category.pk,'title':'Contenido real de prueba','description':'Texto de prueba','validity':'always'}
        data.update(changes)
        response=self.client.post('/api/admin/contents/',data,format='json');self.assertEqual(response.status_code,201,response.data)
        return response.data['id']

    def send(self,pk):
        r=self.client.post(f'/api/admin/contents/{pk}/submit/',{},format='json');self.assertEqual(r.status_code,200,r.data)
        return Approval.objects.filter(content_id=pk).latest('pk')

    def approve(self,pk):
        approval=self.send(pk);self.client.force_login(self.users['admin'])
        r=self.client.post(f'/api/admin/approvals/{approval.pk}/decide/',{'approved':True},format='json');self.assertEqual(r.status_code,200,r.data)
        return approval

    def log(self,**changes):
        values={'uid':'pseudonym-a','user_type':'demo','ip':'192.0.2.1','user_agent':'Windows test','device':'desktop','section':'login','event_type':'access'}
        values.update(changes);return AccessLog.objects.create(**values)

    def csv_rows(self,response):
        body=b''.join(response.streaming_content).decode('utf-8-sig')
        return list(csv.reader(io.StringIO(body)))

    def test_submission_notification_recipients_and_request_idempotency(self):
        pk=self.create();approval=self.send(pk)
        self.assertEqual(Notification.objects.filter(kind='content.submitted').count(),2)
        self.send(pk)
        self.assertEqual(Approval.objects.filter(content_id=pk,state='pending').count(),1)
        self.assertEqual(Notification.objects.filter(kind='content.submitted').count(),2)
        self.assertEqual(approval.proposal['title'],'Contenido real de prueba')

    def test_approval_notification_and_repeated_decision(self):
        pk=self.create();approval=self.approve(pk)
        for _ in range(2):
            self.assertEqual(self.client.post(f'/api/admin/approvals/{approval.pk}/decide/',{'approved':True},format='json').status_code,200)
        self.assertEqual(Publication.objects.filter(content_id=pk).count(),1)
        self.assertEqual(Notification.objects.filter(recipient=self.users['gestor'],kind='content.approved').count(),1)
        self.assertEqual(AuditEvent.objects.filter(action='content.approve').count(),1)

    def test_rejection_reason_and_author_notification(self):
        pk=self.create();approval=self.send(pk);self.client.force_login(self.users['admin'])
        self.assertEqual(self.client.post(f'/api/admin/approvals/{approval.pk}/decide/',{'approved':False},format='json').status_code,400)
        response=self.client.post(f'/api/admin/approvals/{approval.pk}/decide/',{'approved':False,'reason':'Corrija el contacto.'},format='json')
        self.assertEqual(response.status_code,200)
        self.assertIn('Corrija el contacto.',Notification.objects.get(kind='content.rejected').message)
        self.assertEqual(APIClient().get('/api/avisos').data,[])

    def test_expiration_notification_is_unique(self):
        pk=self.create();self.approve(pk)
        Publication.objects.filter(content_id=pk).update(ends_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(register_expirations(),1);self.assertEqual(register_expirations(),0)
        self.assertEqual(Notification.objects.filter(kind='content.expired').count(),1)
        self.assertEqual(APIClient().get('/api/avisos').data,[])

    def test_inbox_isolation_unread_and_read_dates(self):
        pk=self.create();self.approve(pk)
        own=Notification.objects.get(kind='content.approved');other=Notification.objects.filter(recipient=self.users['admin']).first()
        self.client.force_login(self.users['gestor'])
        self.assertEqual(self.client.get('/api/admin/notifications/unread/').data['count'],1)
        self.assertEqual(self.client.get(f'/api/admin/notifications/{other.pk}/').status_code,404)
        self.assertEqual(self.client.post(f'/api/admin/notifications/{other.pk}/mark_read/',{}).status_code,404)
        self.assertEqual(self.client.post(f'/api/admin/notifications/{own.pk}/mark_read/',{}).status_code,200)
        own.refresh_from_db();date=own.read_at;self.assertIsNotNone(date)
        self.client.post(f'/api/admin/notifications/{own.pk}/mark_read/',{});own.refresh_from_db();self.assertEqual(own.read_at,date)
        self.assertEqual(self.client.get('/api/admin/notifications/unread/').data['count'],0)
        self.assertEqual(self.client.post('/api/admin/notifications/mark_all_read/',{}).data['marked'],0)
        other.refresh_from_db();self.assertFalse(other.read)
        self.assertEqual(self.client.delete(f'/api/admin/notifications/{own.pk}/').status_code,405)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_demo_mail_after_commit_and_no_duplicate_delivery(self):
        cfg=GlobalSettings.current();cfg.email_notifications=True;cfg.save()
        pk=self.create()
        with self.captureOnCommitCallbacks(execute=True):self.send(pk)
        self.assertEqual(len(mail.outbox),2)
        self.assertTrue(all('PortalInfo UHO' in message.body for message in mail.outbox))
        delivery=MailDelivery.objects.first();self.assertEqual(delivery.state,'sent')
        self.assertFalse(send_delivery(delivery.pk));self.assertEqual(len(mail.outbox),2)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.force_login(self.users['admin'])
            self.client.post(f'/api/admin/contents/{pk}/review/',{'approved':True},format='json')
        self.assertEqual(len(mail.outbox),3)
        self.assertTrue(any(self.users['gestor'].email in message.to for message in mail.outbox))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_mail_failure_records_safe_error_and_can_retry(self):
        cfg=GlobalSettings.current();cfg.email_notifications=True;cfg.save();pk=self.create()
        with patch('apps.notifications.services.EmailMultiAlternatives.send',side_effect=OSError('secret-password-in-error')):
            with self.captureOnCommitCallbacks(execute=True):self.send(pk)
        delivery=MailDelivery.objects.first();self.assertEqual(delivery.state,'failed');self.assertEqual(delivery.error_code,'OSError')
        self.assertNotIn('secret',str(list(MailDelivery.objects.values())))
        self.assertTrue(send_delivery(delivery.pk));delivery.refresh_from_db();self.assertEqual(delivery.attempts,2)

    def test_queue_filters_preview_snapshot_and_permissions(self):
        pk=self.create();approval=self.send(pk)
        self.assertEqual(self.client.get('/api/admin/approvals/').status_code,403)
        self.client.force_login(self.users['admin'])
        response=self.client.get('/api/admin/approvals/',{'category':self.category.pk,'author':self.users['gestor'].pk,'search':'real'})
        self.assertEqual(response.data['count'],1);self.assertEqual(response.data['results'][0]['proposal']['title'],'Contenido real de prueba')
        self.assertEqual(self.client.get('/api/admin/approvals/summary/').data['pending'],1)
        self.assertEqual(self.client.get('/api/admin/approvals/',{'author':999}).data['count'],0)
        self.client.force_login(self.users['gestor']);self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Texto modificado'},format='json')
        self.client.force_login(self.users['admin'])
        historical=self.client.get(f'/api/admin/approvals/{approval.pk}/').data
        self.assertEqual(historical['proposal']['title'],'Contenido real de prueba')
        self.assertEqual(self.client.post(f'/api/admin/approvals/{approval.pk}/decide/',{'approved':True},format='json').status_code,400)

    def test_comparison_preserves_published_version_during_revision(self):
        pk=self.create();self.approve(pk);self.client.force_login(self.users['gestor'])
        self.client.patch(f'/api/admin/contents/{pk}/',{'title':'Propuesta modificada'},format='json')
        value=self.client.get(f'/api/admin/contents/{pk}/comparison/').data
        self.assertEqual(value['approved']['title'],'Contenido real de prueba');self.assertEqual(value['proposed']['title'],'Propuesta modificada')

    def test_public_views_reject_private_content_identity_and_hidden_sections(self):
        pk=self.create();client=APIClient()
        self.assertEqual(client.post('/api/vistas',{'section':'avisos','content':pk},format='json').status_code,400)
        self.assertEqual(client.post('/api/vistas',{'section':'portal','uid':'attacker','user_type':'estudiantes'},format='json').status_code,400)
        self.approve(pk)
        self.assertEqual(client.post('/api/vistas',{'section':'portal','content':pk},format='json').status_code,400)
        self.category.visible=False;self.category.save()
        self.assertEqual(client.post('/api/vistas',{'section':'avisos'},format='json').status_code,400)
        self.assertEqual(ContentView.objects.count(),0)

    def test_view_context_comes_from_server_and_is_linked(self):
        pk=self.create();self.approve(pk);client=APIClient()
        r=client.post('/api/vistas',{'section':'avisos','content':pk},format='json',REMOTE_ADDR='198.51.100.1',HTTP_X_FORWARDED_FOR='203.0.113.99',HTTP_USER_AGENT='iPhone Test')
        self.assertEqual(r.status_code,201,r.data)
        log=AccessLog.objects.get(event_type='view');self.assertEqual(log.ip,'198.51.100.1');self.assertEqual(log.device,'mobile');self.assertEqual(log.uid,'')
        view=ContentView.objects.get();self.assertEqual(view.access_log_id,log.pk);self.assertEqual(view.category_id,self.category.pk)

    @override_settings(TRUSTED_PROXY_CIDRS=['127.0.0.1/32','198.51.100.0/24'])
    def test_only_explicit_trusted_proxy_hops_are_consumed(self):
        client=APIClient();client.post('/api/vistas',{'section':'portal'},format='json',REMOTE_ADDR='127.0.0.1',HTTP_X_FORWARDED_FOR='192.0.2.5,198.51.100.4')
        self.assertEqual(AccessLog.objects.get().ip,'192.0.2.5')

    def test_view_endpoint_requires_csrf_and_limits_frequency(self):
        client=APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.post('/api/vistas',{'section':'portal'},format='json').status_code,403)
        token=client.get('/api/csrf/').data['csrfToken']
        self.assertEqual(client.post('/api/vistas',{'section':'portal'},format='json',HTTP_X_CSRFTOKEN=token).status_code,201)
        statuses=[client.post('/api/vistas',{'section':'portal'},format='json',HTTP_X_CSRFTOKEN=token,HTTP_X_FORWARDED_FOR=str(i)).status_code for i in range(61)]
        self.assertIn(429,statuses)

    def test_demo_access_uses_current_identity_and_never_client_type(self):
        response=self.client.post('/api/demo/portal-access/',{'uid':'forged','user_type':'estudiantes'},format='json')
        self.assertEqual(response.status_code,201)
        log=AccessLog.objects.get();self.assertTrue(log.uid.startswith('cms:'));self.assertEqual(log.user_type,'demo');self.assertNotIn('gestor',log.uid)
        with override_settings(PRODUCTION=True):self.assertEqual(self.client.post('/api/demo/portal-access/',{}).status_code,403)

    def test_statistics_match_rows_and_exclude_seed_by_default(self):
        self.log();self.log(device='mobile',user_type='estudiantes');self.log(demo=True)
        self.client.post('/api/vistas',{'section':'portal'},format='json')
        self.client.force_login(self.users['admin'])
        value=self.client.get('/api/admin/estadisticas').data
        self.assertEqual(value['accesses'],2);self.assertEqual(value['views'],1)
        self.assertEqual(sum(r['count'] for r in value['by_day']),2)
        self.assertEqual(sum(r['count'] for r in value['by_week']),2)
        self.assertEqual(sum(r['count'] for r in value['by_hour']),2)
        self.assertEqual(self.client.get('/api/admin/estadisticas',{'data_scope':'demo'}).data['accesses'],1)
        self.assertNotIn('pseudonym-a',str(value))

    def test_dashboard_snapshot_and_period_counts(self):
        first=self.create();self.approve(first)
        self.client.force_login(self.users['gestor']);second=self.create();self.send(second);self.create()
        data=self.client.get('/api/admin/dashboard/').data
        self.assertEqual(data['contents'],3);self.assertEqual(data['active'],1);self.assertEqual(data['inactive'],2)
        self.assertEqual(data['pending'],1);self.assertEqual(data['requests_pending'],1);self.assertIsNone(data['accesses'])
        self.assertIsNone(data['users']);self.assertEqual(data['created_in_period'],3)

    def test_period_dates_timezone_and_validation(self):
        now=timezone.make_aware(datetime(2026,11,14,13,0))
        for value,day in [('today',14),('7d',8),('30d',16),('month',1)]:
            period=period_from({'period':value},now)
            self.assertEqual(period['start'].day,day);self.assertEqual(period['start'].hour,0)
            self.assertEqual(period['timezone'],'America/Havana')
        period=period_from({'period':'custom','date_from':'2026-11-01','date_to':'2026-11-02'},now)
        self.assertEqual((period['end']-period['start']).days,2)
        self.client.force_login(self.users['admin'])
        self.assertEqual(self.client.get('/api/admin/estadisticas',{'period':'custom','date_from':'2026-11-02','date_to':'2026-11-01'}).status_code,400)

    def test_logs_and_reports_are_restricted_by_role(self):
        for path in ['/api/admin/logs','/api/admin/estadisticas','/api/admin/security-alerts/','/api/admin/reports/general/','/api/admin/approvals/','/api/admin/audit/']:
            self.assertEqual(self.client.get(path).status_code,403,path)
        self.client.force_login(self.users['admin'])
        self.assertEqual(self.client.get('/api/admin/logs').status_code,200)
        self.assertEqual(self.client.get('/api/admin/reports/audit/').status_code,403)

    def test_security_rules_are_idempotent_and_reviewable(self):
        cfg=GlobalSettings.current();seconds=cfg.security_window_minutes*60
        anchor=datetime.fromtimestamp(int(timezone.now().timestamp())//seconds*seconds,tz=dt_timezone.utc)
        for i in range(4):
            log=self.log(ip=f'192.0.2.{i+1}',user_agent=f'DEVICE {i}')
            AccessLog.objects.filter(pk=log.pk).update(created_at=anchor+timedelta(seconds=i))
        period=period_from({'period':'7d'})
        self.assertEqual(detect_alerts(period),2);self.assertEqual(detect_alerts(period),0)
        self.client.force_login(self.users['admin']);alert=SecurityAlert.objects.first()
        self.assertEqual(self.client.get('/api/admin/security-alerts/',{'priority':alert.priority,'reviewed':'false'}).data['count'],2)
        self.assertEqual(self.client.post(f'/api/admin/security-alerts/{alert.pk}/mark_reviewed/',{}).status_code,200)
        alert.refresh_from_db();self.assertIsNotNone(alert.reviewed_at)
        self.assertEqual(self.client.get('/api/admin/security-alerts/',{'reviewed':'true'}).data['count'],1)
        self.assertIn('no demuestra',alert.evidence['notice'])

    def test_security_does_not_flag_anonymous_or_single_device_patterns(self):
        for i in range(5):self.log(uid='');self.log(uid=f'isolated-{i}')
        self.assertEqual(detect_alerts(period_from({})),0)

    def test_activity_spike_requires_available_history_and_configured_threshold(self):
        cfg=GlobalSettings.current();cfg.security_activity_threshold=5;cfg.security_activity_multiplier=3;cfg.save()
        seconds=cfg.security_window_minutes*60;anchor=datetime.fromtimestamp(int(timezone.now().timestamp())//seconds*seconds,tz=dt_timezone.utc)
        log=self.log();AccessLog.objects.filter(pk=log.pk).update(created_at=anchor-timedelta(seconds=1))
        for i in range(5):
            log=self.log();AccessLog.objects.filter(pk=log.pk).update(created_at=anchor+timedelta(seconds=i))
        self.assertEqual(detect_alerts(period_from({})),1);self.assertEqual(SecurityAlert.objects.get().kind,'activity_spike')
        self.client.force_login(self.users['admin']);self.assertEqual(self.client.patch('/api/admin/settings/',{'security_ip_threshold':2}).status_code,403)
        self.client.force_login(self.users['superadmin']);self.assertEqual(self.client.patch('/api/admin/settings/',{'security_ip_threshold':1}).status_code,400)

    def test_audit_before_after_excludes_credentials_and_is_read_only(self):
        self.client.force_login(self.users['superadmin'])
        self.client.patch('/api/admin/settings/',{'retention_days':120},format='json')
        event=AuditEvent.objects.get(action='configuration.update')
        self.assertEqual(event.metadata['before']['retention_days'],90);self.assertEqual(event.metadata['after']['retention_days'],120)
        query={'entity':'configuration','action':'configuration.update','actor':self.users['superadmin'].pk,'period':'today'}
        self.assertEqual(self.client.get('/api/admin/audit/',query).data['count'],1)
        self.assertEqual(self.client.patch(f'/api/admin/audit/{event.pk}/',{'metadata':{}},format='json').status_code,405)
        self.assertEqual(self.client.delete(f'/api/admin/audit/{event.pk}/').status_code,405)
        self.assertNotIn('password',str(event.metadata))

    def test_csv_utf8_formula_protection_and_filters(self):
        self.client.force_login(self.users['admin'])
        self.create(title='=HYPERLINK("x")')
        response=self.client.get('/api/admin/reports/contents/',{'file_format':'csv','category':self.category.pk,'state':'draft'})
        self.assertEqual(response.status_code,200);rows=self.csv_rows(response)
        self.assertEqual(len(rows),2);self.assertTrue(rows[1][2].startswith("'="))
        for text in ['=1+1',' +cmd','-cmd','@sum','\tname','\ufeff=cmd']:self.assertTrue(safe_csv(text).startswith("'"))
        self.assertEqual(safe_csv(-3),-3)

    def test_access_export_matches_filters(self):
        self.log(device='mobile');self.log(device='desktop');self.log(device='mobile',demo=True)
        self.client.force_login(self.users['admin'])
        rows=self.csv_rows(self.client.get('/api/admin/reports/accesses/',{'device':'mobile'}))
        self.assertEqual(len(rows),2);self.assertEqual(rows[1][5],'mobile')
        self.assertEqual(self.client.get('/api/admin/access-logs/',{'device':'mobile'}).data['count'],1)

    def test_content_report_respects_demo_source(self):
        self.client.force_login(self.users['admin'])
        pk=self.create();Content.objects.filter(pk=pk).update(seed_key='report-demo-source')
        self.assertEqual(len(self.csv_rows(self.client.get('/api/admin/reports/contents/',{'data_scope':'real'}))),1)
        self.assertEqual(len(self.csv_rows(self.client.get('/api/admin/reports/contents/',{'data_scope':'demo'}))),2)

    def test_all_report_kinds_csv_and_pdf_are_valid(self):
        from pypdf import PdfReader
        self.client.force_login(self.users['superadmin']);self.log();AuditEvent.objects.create(action='test.action',entity='test')
        self.create()
        survey=self.create(category=self.survey_category.pk,details={'external_url':'https://example.invalid/survey','questions':[]})
        for kind in ['general','accesses','contents','surveys','audit','security']:
            params={'file_format':'csv','content':survey}
            response=self.client.get('/api/admin/reports/'+kind+'/',params)
            self.assertEqual(response.status_code,200,kind);self.assertGreaterEqual(len(self.csv_rows(response)),1)
            params['file_format']='pdf';response=self.client.get('/api/admin/reports/'+kind+'/',params)
            self.assertEqual(response.status_code,200,kind);self.assertTrue(response.content.startswith(b'%PDF-'))
            reader=PdfReader(io.BytesIO(response.content));self.assertGreater(len(reader.pages),0)
            self.assertIn('PortalInfo UHO',reader.pages[0].extract_text())

    def test_pdf_pagination_and_explicit_size_limit(self):
        from pypdf import PdfReader
        self.client.force_login(self.users['superadmin'])
        AuditEvent.objects.bulk_create([AuditEvent(action=f'action-{i}',entity='batch',metadata={'description':'Prueba de informe paginado.'}) for i in range(120)])
        response=self.client.get('/api/admin/reports/audit/',{'file_format':'pdf','entity':'batch'})
        self.assertEqual(response.status_code,200);self.assertGreater(len(PdfReader(io.BytesIO(response.content)).pages),1)
        with override_settings(REPORT_PDF_MAX_ROWS=1):self.assertEqual(self.client.get('/api/admin/reports/audit/',{'file_format':'pdf','entity':'batch'}).status_code,400)

    def test_retention_defaults_to_dry_run_and_requires_explicit_authority(self):
        log=self.log();old=timezone.now()-timedelta(days=100);AccessLog.objects.filter(pk=log.pk).update(created_at=old)
        event=AuditEvent.objects.create(action='old');AuditEvent.objects.filter(pk=event.pk).update(created_at=old)
        call_command('maintain_logs',stdout=io.StringIO());self.assertTrue(AccessLog.objects.filter(pk=log.pk).exists())
        with self.assertRaises(CommandError):call_command('maintain_logs',apply=True,stdout=io.StringIO())
        self.assertTrue(AccessLog.objects.filter(pk=log.pk).exists())
        call_command('maintain_logs',apply=True,authorized_by=self.users['superadmin'].pk,confirm_days=90,stdout=io.StringIO())
        self.assertFalse(AccessLog.objects.filter(pk=log.pk).exists());self.assertFalse(AuditEvent.objects.filter(pk=event.pk).exists())
        self.assertTrue(AuditEvent.objects.filter(action='retention.applied').exists())

    def test_demo_activity_seed_is_identified_idempotent_and_preserves_manual_rows(self):
        manual=self.log(uid='manual')
        with TemporaryDirectory(dir=settings.BASE_DIR.parent/'.local') as directory:
            with override_settings(BASE_DIR=Path(directory)/'backend'):
                call_command('seed_demo',with_activity=True,stdout=io.StringIO())
                counts=(AccessLog.objects.count(),ContentView.objects.count(),Notification.objects.count(),Submission.objects.count(),SecurityAlert.objects.count())
                call_command('seed_demo',with_activity=True,stdout=io.StringIO())
                self.assertEqual(counts,(AccessLog.objects.count(),ContentView.objects.count(),Notification.objects.count(),Submission.objects.count(),SecurityAlert.objects.count()))
        self.assertTrue(AccessLog.objects.filter(pk=manual.pk,uid='manual').exists())
        self.assertTrue(Submission.objects.filter(demo=True).exists());self.assertTrue(SecurityAlert.objects.filter(demo=True).exists())
        self.client.force_login(self.users['admin']);self.assertEqual(self.client.get('/api/admin/estadisticas').data['accesses'],1)

    def test_survey_participants_versions_multiple_percentages_and_open_pagination(self):
        survey=self.create(category=self.survey_category.pk,details={'external_url':'','questions':[
            {'text':'Múltiple','kind':'multiple','required':True,'options':[{'text':'A'},{'text':'B'}]},
            {'text':'Comentario','kind':'open','required':True,'options':[]}]})
        self.approve(survey)
        visitor=APIClient()
        def vote():
            data=APIClient().get('/api/encuestas').data[0]['details']['questions']
            return visitor.post(f'/api/encuestas/{survey}/respuestas',{'answers':[
                {'question':data[0]['id'],'options':[o['id'] for o in data[0]['options']]},
                {'question':data[1]['id'],'value':'Comentario sin identidad personal'}]},format='json')
        self.assertEqual(vote().status_code,201)
        self.client.patch(f'/api/admin/contents/{survey}/',{'title':'Corrección de título'},format='json')
        self.assertEqual(vote().status_code,201)
        results=self.client.get(f'/api/admin/contents/{survey}/results/').data
        self.assertEqual(results['total'],2);self.assertEqual(results['participants'],1);self.assertEqual(results['answers_total'],4)
        self.assertEqual(sum(o['percentage'] for o in results['versions'][0]['questions'][0]['options']),200)
        opened=self.client.get(f'/api/admin/contents/{survey}/open_answers/').data
        self.assertEqual(opened['count'],2);self.assertNotIn('respondent_key',str(opened))
        self.client.force_login(self.users['gestor']);self.assertEqual(self.client.get(f'/api/admin/contents/{survey}/open_answers/').status_code,403)

    def test_notification_list_does_not_query_each_mail_delivery(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        Notification.objects.create(recipient=self.users['gestor'],kind='test',title='Notificación',message='Texto')
        with CaptureQueriesContext(connection) as baseline:self.client.get('/api/admin/notifications/')
        Notification.objects.bulk_create([Notification(recipient=self.users['gestor'],kind='test',title='Notificación',message='Texto') for _ in range(14)])
        with CaptureQueriesContext(connection) as captured:response=self.client.get('/api/admin/notifications/')
        self.assertEqual(response.status_code,200);self.assertEqual(len(response.data['results']),15)
        self.assertLessEqual(len(captured),len(baseline))

    def test_mail_flag_can_be_enabled_without_real_smtp_and_audits_config_change(self):
        self.client.force_login(self.users['superadmin'])
        response=self.client.patch('/api/admin/settings/',{'email_notifications':True},format='json')
        self.assertEqual(response.status_code,200);self.assertTrue(GlobalSettings.current().email_notifications)
        self.assertIn(settings.EMAIL_MODE,['file','console','memory'])
        self.assertTrue(AuditEvent.objects.filter(action='configuration.update').exists())


class ConcurrentApprovalTests(TransactionTestCase):
    def test_two_decisions_serialize_and_publish_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        role=Role.objects.create(code='admin',name='Admin');manager_role=Role.objects.create(code='gestor',name='Gestor')
        manager=User.objects.create_user(username='manager',email='manager@uho.edu.cu',role=manager_role,demo=True)
        admins=[User.objects.create_user(username=f'admin-{i}',email=f'admin-{i}@uho.edu.cu',role=role,demo=True) for i in range(2)]
        category=Category.objects.create(name='Avisos concurrentes',slug='avisos',content_type='notice')
        item=Content.objects.create(category=category,title='Revisión concurrente',description='Texto',author=manager,state='pending',validity='always')
        approval=Approval.objects.create(content=item,requested_by=manager,version=1)
        barrier=Barrier(2)
        def decide(admin_id):
            close_old_connections()
            try:
                client=APIClient();client.force_login(User.objects.get(pk=admin_id));barrier.wait(timeout=10)
                return client.post(f'/api/admin/approvals/{approval.pk}/decide/',{'approved':True},format='json').status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(decide,[u.pk for u in admins]))
        self.assertEqual(sorted(statuses),[200,400]);self.assertEqual(Publication.objects.filter(content=item).count(),1)
        self.assertEqual(Notification.objects.filter(kind='content.approved',recipient=manager).count(),1)
