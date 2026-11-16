from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User, Role, Grant
from apps.accounts.permissions import category_allowed
from apps.audit.models import AuditEvent
from apps.catalogs.models import Category, CatalogType, CatalogItem
from apps.content.models import Content
from apps.settings_app.models import GlobalSettings


class SecurityTests(TestCase):
    def test_logout_clears_disabled_session_and_still_requires_csrf(self):
        client=APIClient(enforce_csrf_checks=True)
        client.force_login(self.users['gestor'])
        self.users['gestor'].is_active=False;self.users['gestor'].save()
        self.assertEqual(client.post('/auth/logout',{},format='json').status_code,403)
        token=client.get('/api/csrf/').data['csrfToken']
        self.assertEqual(client.post('/auth/logout',{},format='json',HTTP_X_CSRFTOKEN=token).status_code,200)
        self.assertEqual(client.get('/api/me/').status_code,403)

    def test_unknown_environment_does_not_silently_enable_demo(self):
        import os,runpy
        from unittest.mock import patch
        with patch.dict(os.environ,{'APP_ENV':'prod'}):
            with self.assertRaises(ImproperlyConfigured):runpy.run_path(str(settings.BASE_DIR/'config/settings.py'))

    def test_private_endpoints_forbid_browser_cache(self):
        self.as_role('superadmin')
        for path in ['/api/me/','/api/admin/users/','/api/admin/settings/','/portal-auth/session']:
            self.assertEqual(self.client.get(path)['Cache-Control'],'no-store')

    def test_login_input_is_bounded(self):
        self.assertEqual(self.client.post('/auth/login',{'email':'a@uho.edu.cu','password':'x'*257}).status_code,400)

    def test_default_validity_rejects_unrepresentable_ranges(self):
        self.as_role('superadmin')
        self.assertEqual(self.client.patch('/api/admin/settings/',{'default_validity_days':1000000},format='json').status_code,400)

    @classmethod
    def setUpTestData(cls):
        cls.roles={code:Role.objects.create(code=code,name=label) for code,label in Role.Code.choices}
        cls.users={}
        for code,role in cls.roles.items():
            cls.users[code]=User.objects.create_user(username=code,email=f'{code}@uho.edu.cu',password='Test-secret-582!',role=role,demo=True,protected=code=='superadmin')
        cls.a=Category.objects.create(name='Noticias',slug='noticias')
        cls.b=Category.objects.create(name='Eventos',slug='eventos')
        cls.users['gestor'].categories.add(cls.a)
        Grant.objects.create(role=cls.roles['gestor'],category=cls.a,operation='edit')

    def setUp(self):
        self.client=APIClient()

    def as_role(self, role):
        self.client.force_login(self.users[role])

    def test_postgresql_and_tables(self):
        self.assertEqual(connection.vendor,'postgresql')
        self.assertIn('content_content',connection.introspection.table_names())

    def test_valid_login_and_logout_revokes_session(self):
        self.assertEqual(self.client.post('/auth/login',{'email':'gestor@uho.edu.cu','password':'Test-secret-582!'}).status_code,200)
        old=self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertEqual(self.client.get('/api/me/').status_code,200)
        self.assertEqual(self.client.post('/auth/logout').status_code,200)
        self.client.cookies[settings.SESSION_COOKIE_NAME]=old
        self.assertEqual(self.client.get('/api/me/').status_code,403)
        self.assertTrue(AuditEvent.objects.filter(action='auth.logout').exists())

    def test_invalid_and_unregistered_identity(self):
        for email,password in [('gestor@uho.edu.cu','incorrect'),('unknown@uho.edu.cu','Test-secret-582!')]:
            response=self.client.post('/auth/login',{'email':email,'password':password})
            self.assertEqual(response.status_code,403)
            self.assertEqual(response.json()['detail'],'No tiene acceso a este sistema')

    def test_all_roles_can_authenticate(self):
        for code,user in self.users.items():
            response=self.client.post('/auth/login',{'email':user.email,'password':'Test-secret-582!'})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.data['role_code'],code)
            self.assertEqual(self.client.post('/auth/logout').status_code,200)

    def test_deactivation_invalidates_existing_session(self):
        self.as_role('gestor')
        user=self.users['gestor']; user.is_active=False; user.save()
        self.assertEqual(self.client.get('/api/admin/dashboard/').status_code,403)
        self.assertEqual(self.client.post('/auth/login',{'email':user.email,'password':'Test-secret-582!'}).status_code,403)

    def test_weak_demo_password_rejected(self):
        self.as_role('superadmin')
        response=self.client.post('/api/admin/users/',{'email':'weak@uho.edu.cu','role':self.roles['gestor'].pk,'password':'123'})
        self.assertEqual(response.status_code,400)
        self.assertFalse(User.objects.filter(email='weak@uho.edu.cu').exists())

    def test_unauthorized_and_disabled_accounts(self):
        user=self.users['gestor']; user.authorized=False; user.save()
        self.assertEqual(self.client.post('/auth/login',{'email':user.email,'password':'Test-secret-582!'}).status_code,403)
        self.as_role('gestor')
        self.assertEqual(self.client.get('/api/admin/dashboard/').status_code,403)

    def test_ip_lockout(self):
        GlobalSettings.objects.create(login_attempts=2)
        for _ in range(2):
            self.assertEqual(self.client.post('/auth/login',{'email':'unknown@uho.edu.cu','password':'bad'}).status_code,403)
        self.assertEqual(self.client.post('/auth/login',{'email':'gestor@uho.edu.cu','password':'Test-secret-582!'}).status_code,429)

    def test_login_requires_csrf(self):
        client=APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.post('/auth/login',{'email':'gestor@uho.edu.cu','password':'Test-secret-582!'}).status_code,403)
        token=client.get('/api/csrf/').json()['csrfToken']
        self.assertEqual(client.post('/auth/login',{'email':'gestor@uho.edu.cu','password':'Test-secret-582!'},HTTP_X_CSRFTOKEN=token).status_code,200)

    def test_protected_endpoints(self):
        for endpoint in ['users/','categories/','permissions/','catalog-items/','audit/','settings/','dashboard/']:
            self.assertEqual(self.client.get('/api/admin/'+endpoint).status_code,403)

    def test_manager_cannot_modify_categories_or_users(self):
        self.as_role('gestor')
        for endpoint in [f'categories/{self.a.pk}/',f'categories/{self.b.pk}/',f'users/{self.users["admin"].pk}/']:
            self.assertEqual(self.client.patch('/api/admin/'+endpoint,{'name':'intrusion'}).status_code,403)

    def test_category_grants_require_assignment_and_operation(self):
        user=self.users['gestor']
        self.assertTrue(category_allowed(user,self.a,'edit'))
        self.assertFalse(category_allowed(user,self.a,'delete'))
        Grant.objects.create(user=user,category=self.b,operation='edit')
        self.assertFalse(category_allowed(user,self.b,'edit'))
        user.categories.add(self.b)
        self.assertTrue(category_allowed(user,self.b,'edit'))

    def test_admin_cannot_escalate(self):
        self.as_role('admin')
        self.assertEqual(self.client.post('/api/admin/users/',{'email':'new@uho.edu.cu','role':self.roles['superadmin'].pk}).status_code,403)
        self.assertEqual(self.client.patch(f'/api/admin/users/{self.users["gestor"].pk}/',{'role':self.roles['admin'].pk}).status_code,403)
        self.assertEqual(self.client.post('/api/admin/permissions/',{'role':self.roles['admin'].pk,'category':self.a.pk,'operation':'edit'}).status_code,403)

    def test_create_update_user_and_audit(self):
        self.as_role('admin')
        response=self.client.post('/api/admin/users/',{'email':'new@uho.edu.cu','role':self.roles['gestor'].pk,'password':'New-secret-987!','categories':[self.a.pk]},format='json')
        self.assertEqual(response.status_code,201,response.data)
        user=User.objects.get(pk=response.data['id'])
        self.assertTrue(user.check_password('New-secret-987!'))
        self.assertNotIn('password',response.data)
        self.assertEqual(self.client.patch(f'/api/admin/users/{user.pk}/',{'is_active':False}).status_code,200)
        self.assertTrue(AuditEvent.objects.filter(action='user.update').exists())
        self.assertNotIn('New-secret',str(list(AuditEvent.objects.values())))

    def test_email_validation(self):
        self.as_role('superadmin')
        self.assertEqual(self.client.post('/api/admin/users/',{'email':'x@example.com','role':self.roles['gestor'].pk}).status_code,400)

    def test_superadmin_protection(self):
        self.as_role('superadmin'); pk=self.users['superadmin'].pk
        self.assertEqual(self.client.delete(f'/api/admin/users/{pk}/').status_code,403)
        for payload in [{'is_active':False},{'authorized':False},{'role':self.roles['gestor'].pk}]:
            self.assertEqual(self.client.patch(f'/api/admin/users/{pk}/',payload).status_code,400)

    def test_catalog_crud_and_integrity(self):
        self.as_role('admin')
        response=self.client.post('/api/admin/catalog-types/',{'name':'Áreas','slug':'areas'})
        self.assertEqual(response.status_code,201)
        cat=response.data['id']
        response=self.client.post('/api/admin/catalog-items/',{'catalog':cat,'name':'Ejemplo'})
        self.assertEqual(response.status_code,201)
        pk=response.data['id']
        self.assertEqual(self.client.patch(f'/api/admin/catalog-items/{pk}/',{'name':'Modificado'}).status_code,200)
        self.assertEqual(self.client.delete(f'/api/admin/catalog-types/{cat}/').status_code,400)
        self.assertEqual(self.client.delete(f'/api/admin/catalog-items/{pk}/').status_code,204)
        self.assertEqual(self.client.delete(f'/api/admin/catalog-types/{cat}/').status_code,204)

    def test_settings_persist_and_validate(self):
        self.as_role('superadmin')
        self.assertEqual(self.client.patch('/api/admin/settings/',{'max_questions':12}).status_code,200)
        self.assertEqual(self.client.get('/api/admin/settings/').data['max_questions'],12)
        self.assertEqual(self.client.patch('/api/admin/settings/',{'login_attempts':0}).status_code,400)
        self.as_role('admin')
        self.assertEqual(self.client.patch('/api/admin/settings/',{'login_attempts':2}).status_code,403)

    def test_category_crud_and_public_config(self):
        self.as_role('superadmin')
        response=self.client.post('/api/admin/categories/',{'name':'Logros','slug':'logros'})
        self.assertEqual(response.status_code,201)
        pk=response.data['id']
        self.as_role('admin')
        self.assertEqual(self.client.patch(f'/api/admin/categories/{pk}/',{'max_visible':2,'visible':False}).status_code,200)
        self.assertNotIn('logros',[x['slug'] for x in self.client.get('/api/config').data['sections']])
        self.assertEqual(self.client.patch(f'/api/admin/categories/{pk}/',{'slug':'bad'}).status_code,403)
        self.assertEqual(self.client.delete(f'/api/admin/categories/{pk}/').status_code,403)
        self.as_role('superadmin')
        self.assertEqual(self.client.delete(f'/api/admin/categories/{pk}/').status_code,204)

    def test_audit_read_only_and_restricted(self):
        self.as_role('admin')
        self.assertEqual(self.client.get('/api/admin/audit/').status_code,403)
        self.as_role('superadmin')
        self.assertEqual(self.client.get('/api/admin/audit/').status_code,200)
        self.assertEqual(self.client.post('/api/admin/audit/',{}).status_code,405)

    def test_visibility_is_independent_of_editorial_state(self):
        from datetime import timedelta
        item=Content.objects.create(category=self.a,title='Test',description='Text',author=self.users['gestor'],state='approved')
        from apps.content.services import publish
        publish(item,self.users['admin'])
        self.assertTrue(item.effectively_visible)
        item.live_publication.ends_at=timezone.now()-timedelta(seconds=1)
        item.live_publication.save()
        self.assertFalse(item.effectively_visible)
        item.live_publication=None; item.state='pending'; item.save()
        self.assertFalse(item.effectively_visible)

    def test_dashboard_real_counts_and_pagination(self):
        self.as_role('superadmin')
        self.assertEqual(self.client.get('/api/admin/dashboard/').data['users'],3)
        self.assertEqual(self.client.get('/api/admin/users/?search=gestor').data['count'],1)

    def test_demo_provider_never_runs_in_production(self):
        from .providers import get_provider, AGAAuthProvider
        with override_settings(PRODUCTION=True, AUTH_PROVIDER='aga'):
            self.assertIsInstance(get_provider(),AGAAuthProvider)
        with override_settings(PRODUCTION=True, AUTH_PROVIDER='demo'):
            from .providers import ProviderUnavailable
            with self.assertRaises(ProviderUnavailable): get_provider()

    def test_swagger_and_schema(self):
        self.assertEqual(self.client.get('/api/docs/').status_code,200)
        self.assertEqual(self.client.get('/api/schema/').status_code,200)
