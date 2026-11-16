import json
import time
from datetime import timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User, Role
from apps.analytics.models import AccessLog, ContentView
from apps.audit.models import AuditEvent
from apps.catalogs.models import Category
from apps.content.models import Content, Publication, Survey, Question, Option, Submission
from apps.content.services import snapshot
from apps.settings_app.models import GlobalSettings
from .identity import SESSION_KEY


class PortalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role = Role.objects.create(code='admin', name='Admin')
        cls.admin = User.objects.create_user(username='admin', email='admin@uho.edu.cu', role=cls.role, demo=True)
        GlobalSettings.current()

    def setUp(self):
        cache.clear()
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.users_file = Path(self.temp.name) / 'portal-demo-users.json'
        self.users_file.write_text(json.dumps({'demo.estudiante': {'active': True, 'full_name': 'Estudiante DEMO',
            'user_type': 'estudiantes', 'password_hash': make_password('Only-test-234!')}}), encoding='utf-8')
        self.override = override_settings(PORTAL_DEMO_USERS_FILE=self.users_file, PORTAL_AUTH_MODE='demo', PRODUCTION=False)
        self.override.enable(); self.addCleanup(self.override.disable)
        self.client = APIClient(enforce_csrf_checks=True)
        self.token = self.client.get('/portal-auth/session').data['csrfToken']

    def login(self, password='Only-test-234!', **extra):
        return self.client.post('/portal-auth/session', {'username': 'demo.estudiante', 'password': password},
            format='json', HTTP_X_CSRFTOKEN=self.token, **extra)

    def publish(self, slug='avisos', kind='notice', title='Contenido publicado'):
        category, _ = Category.objects.get_or_create(slug=slug, defaults={'name': slug, 'content_type': kind, 'max_visible': 10})
        item = Content.objects.create(category=category, author=self.admin, title=title, description='Texto autorizado',
            starts_at=timezone.now()-timedelta(days=1), state='approved')
        if kind == 'survey':
            survey = Survey.objects.create(content=item)
            for index, qkind in enumerate(['single', 'multiple', 'open']):
                q = Question.objects.create(survey=survey, text=qkind, kind=qkind, required=True, position=index)
                if qkind != 'open': Option.objects.bulk_create([Option(question=q,text='A'), Option(question=q,text='B')])
        publication = Publication.objects.create(content=item, category=category, version=1, data=snapshot(item),
            starts_at=item.starts_at, approved_by=self.admin)
        item.live_publication = publication; item.save()
        return item

    def test_shipped_html_self_contained_and_bounded(self):
        response = self.client.get('/portal/')
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.content), 204800)
        html = response.content.decode()
        for text in ['id="login-form"', 'id="username"', 'id="password"', 'id="navigation"', 'id="privacy-title"']:
            self.assertIn(text, html)
        for forbidden in ['<script src=', '<link ', '<img', '<iframe', '@import', 'localStorage', 'sessionStorage', 'Only-test-234!']:
            self.assertNotIn(forbidden, html)
        self.assertIn("frame-ancestors 'none'", response['Content-Security-Policy'])
        self.assertEqual(response['Cache-Control'], 'no-cache')

    def test_valid_login_identity_logs_and_no_admin_rights(self):
        result = self.login()
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data['authenticated'])
        self.assertFalse(result.data['network_access_granted'])
        self.assertEqual(result.data['identity']['full_name'], 'Estudiante DEMO')
        self.assertEqual(self.client.get('/api/admin/contents/').status_code, 403)
        self.assertEqual(User.objects.count(), 1)
        log = AccessLog.objects.get(event_type='access')
        self.assertEqual(log.user_type, 'demo_estudiantes')
        self.assertTrue(log.uid.startswith('portal-demo:'))
        self.assertNotIn('demo.estudiante', log.uid)
        self.assertEqual(log.ip, '127.0.0.1')
        audit = AuditEvent.objects.get(action='portal_auth.login')
        self.assertIsNone(audit.actor)
        self.assertNotIn('password', json.dumps(audit.metadata))
        self.assertIn('no-store', result['Cache-Control'])

    def test_failed_login_never_records_password_or_username(self):
        result = self.login('wrong-super-private')
        self.assertEqual(result.status_code, 403)
        self.assertFalse(self.client.get('/portal-auth/session').data['authenticated'])
        event = AuditEvent.objects.get(action='portal_auth.failed')
        self.assertEqual(event.metadata, {})
        self.assertEqual(AccessLog.objects.count(), 0)

    def test_ip_lockout_configurable_and_expires(self):
        cfg = GlobalSettings.current(); cfg.login_attempts = 2; cfg.lockout_seconds = 30; cfg.save()
        self.assertEqual(self.login('wrong').status_code, 403)
        self.assertEqual(self.login('wrong').status_code, 403)
        blocked = self.login()
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked['Retry-After'], '30')
        AuditEvent.objects.filter(action='portal_auth.failed').update(created_at=timezone.now()-timedelta(seconds=31))
        self.assertEqual(self.login().status_code, 200)

    def test_csrf_login_logout_and_cross_origin(self):
        self.assertEqual(self.client.post('/portal-auth/session', {}, format='json').status_code, 403)
        self.assertEqual(self.login(HTTP_ORIGIN='https://evil.example').status_code, 403)
        self.login()
        self.assertEqual(self.client.post('/portal-auth/logout', {}, format='json').status_code, 403)

    def test_logout_invalidates_previous_cookie_and_retains_cms(self):
        self.client.force_login(self.admin)
        self.token = self.client.get('/portal-auth/session').data['csrfToken']
        self.login()
        cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        result = self.client.post('/portal-auth/logout', {}, format='json', HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(result.status_code, 200)
        self.assertFalse(self.client.get('/portal-auth/session').data['authenticated'])
        self.assertEqual(self.client.get('/api/me/').status_code, 200)
        replay = APIClient(); replay.cookies[settings.SESSION_COOKIE_NAME] = cookie
        self.assertFalse(replay.get('/portal-auth/session').data['authenticated'])
        self.assertEqual(replay.get('/api/me/').status_code, 403)

    def test_expired_unknown_and_revoked_sessions(self):
        for state in [{'identifier': 'missing', 'expires': time.time()+60},
                {'identifier': 'demo.estudiante', 'expires': time.time()-1}]:
            session = self.client.session; session[SESSION_KEY] = state; session.save()
            self.assertFalse(self.client.get('/portal-auth/session').data['authenticated'])
        self.login()
        rows = json.loads(self.users_file.read_text()); rows['demo.estudiante']['active'] = False
        self.users_file.write_text(json.dumps(rows))
        self.assertFalse(self.client.get('/portal-auth/session').data['authenticated'])

    def test_cms_login_does_not_create_visitor_session(self):
        self.client.force_login(self.admin)
        self.assertFalse(self.client.get('/portal-auth/session').data['authenticated'])

    @override_settings(PORTAL_AUTH_MODE='institutional')
    def test_institutional_mode_fails_closed_without_network(self):
        with patch('socket.create_connection', side_effect=AssertionError('No network')):
            response = self.login()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(AccessLog.objects.count(), 0)

    def test_contents_failure_leaves_authentication_operational(self):
        Category.objects.create(name='Noticias',slug='noticias',content_type='news')
        with patch('apps.content.views.visible_publications', side_effect=RuntimeError('Simulated editorial outage')):
            browser = APIClient(); browser.raise_request_exception = False
            self.assertEqual(browser.get('/api/noticias').status_code, 500)
            self.assertEqual(self.client.get('/portal/').status_code, 200)
            self.assertEqual(self.login().status_code, 200)
            self.assertTrue(self.client.get('/portal-auth/session').data['authenticated'])

    def test_public_visibility_pending_expired_hidden_and_category_limits(self):
        visible = self.publish()
        hidden = self.publish(title='Oculto'); hidden.manual_active = False; hidden.save()
        expired = self.publish(title='Vencido')
        expired.live_publication.ends_at = timezone.now()-timedelta(hours=1); expired.live_publication.save()
        pending = self.publish(title='Pendiente'); pending.live_publication = None; pending.state = 'pending'; pending.save()
        self.assertEqual([row['id'] for row in self.client.get('/api/avisos').data], [visible.pk])
        visible.category.visible = False; visible.category.save()
        self.assertEqual(self.client.get('/api/avisos').data, [])
        self.assertEqual(self.client.get('/api/config').data['sections'], [])
        self.assertEqual(self.client.get('/api/categorias').data, [])

    def test_new_category_discovery_metadata_only_and_generic_endpoint(self):
        item = self.publish('becas-nuevas', 'generic')
        config = self.client.get('/api/config').data
        self.assertEqual(config['sections'][0]['slug'], 'becas-nuevas')
        self.assertNotIn('login_attempts', str(config))
        self.assertEqual(self.client.get('/api/categorias?include_contents=false').data[0]['contents'], [])
        self.assertEqual(self.client.get('/api/categorias').data[0]['contents'][0]['id'], item.pk)
        self.assertEqual(self.client.get('/api/becas-nuevas').data[0]['id'], item.pk)

    def test_portal_views_derive_identity_and_reject_arbitrary_identifiers(self):
        item = self.publish(); self.login()
        self.assertEqual(self.client.post('/api/vistas', {'section': 'avisos', 'uid': 'forged'}, format='json', HTTP_X_CSRFTOKEN=self.token).status_code, 400)
        self.assertEqual(self.client.post('/api/vistas', {'section': 'avisos', 'content': item.pk}, format='json', HTTP_X_CSRFTOKEN=self.token).status_code, 201)
        self.assertEqual(ContentView.objects.get().user_type, 'demo_estudiantes')
        self.assertEqual(self.client.post('/api/vistas', {'section': 'missing'}, format='json', HTTP_X_CSRFTOKEN=self.token).status_code, 400)
        self.assertEqual(self.client.post('/api/vistas', {'section': 'portal'}, format='json').status_code, 403)

    def test_authenticated_survey_uses_visitor_identity_and_deduplicates(self):
        item = self.publish('encuestas', 'survey')
        cfg = GlobalSettings.current(); cfg.vote_requires_auth = True; cfg.save()
        questions = item.live_publication.data['details']['questions']
        answers = [{'question': q['id'], 'value': 'Texto' if q['kind']=='open' else '',
            'options': [] if q['kind']=='open' else [o['id'] for o in q['options'][:(2 if q['kind']=='multiple' else 1)]]} for q in questions]
        url = f'/api/encuestas/{item.pk}/respuestas'
        self.assertEqual(self.client.post(url, {'answers': answers}, format='json', HTTP_X_CSRFTOKEN=self.token).status_code, 403)
        self.login()
        self.assertEqual(self.client.post(url, {'answers': []}, format='json', HTTP_X_CSRFTOKEN=self.token).status_code, 400)
        self.assertEqual(self.client.post(url, {'answers': answers}, format='json', HTTP_X_CSRFTOKEN=self.token).status_code, 201)
        self.assertEqual(self.client.post(url, {'answers': answers}, format='json', HTTP_X_CSRFTOKEN=self.token).status_code, 400)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertNotIn('demo.estudiante', Submission.objects.get().respondent_key)

    def test_seed_is_private_idempotent_and_blocked_in_production(self):
        target = Path(self.temp.name) / 'new-users.json'
        with override_settings(PORTAL_DEMO_USERS_FILE=target):
            output = StringIO(); call_command('seed_portal_demo', stdout=output)
            original = target.read_bytes(); call_command('seed_portal_demo', stdout=output)
            self.assertEqual(original, target.read_bytes())
            self.assertEqual(len(json.loads(original)), 3)
            self.assertTrue(target.with_name('portal-demo-credentials.txt').exists())
            with override_settings(PRODUCTION=True):
                with self.assertRaises(CommandError): call_command('seed_portal_demo', stdout=output)

    def test_explicit_cors_and_no_wildcard(self):
        response = self.client.get('/api/config', HTTP_ORIGIN='https://evil.example')
        self.assertNotIn('Access-Control-Allow-Origin', response)
        with override_settings(CORS_ALLOWED_ORIGINS=['https://portal.example']):
            response = self.client.get('/api/config', HTTP_ORIGIN='https://portal.example')
            self.assertEqual(response['Access-Control-Allow-Origin'], 'https://portal.example')
