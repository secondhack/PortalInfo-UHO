from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.core.cache import cache
from django.db import close_old_connections, connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from apps.audit.models import AuditEvent
from apps.settings_app.models import GlobalSettings


class LoginConcurrencyTests(TransactionTestCase):
    def test_parallel_failed_logins_share_one_ip_budget(self):
        cache.clear()
        cfg=GlobalSettings.current();cfg.login_attempts=1;cfg.save()
        barrier=Barrier(2)
        def attempt(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return APIClient().post('/auth/login',{'email':'nobody@uho.edu.cu','password':'invalid'},format='json').status_code
            finally:connections.close_all()
        with patch('apps.accounts.views.get_provider') as provider:
            provider.return_value.authenticate.return_value=None
            with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(attempt,range(2)))
        self.assertEqual(sorted(statuses),[403,429])
        self.assertEqual(AuditEvent.objects.filter(action='auth.failed').count(),1)
        self.assertEqual(AuditEvent.objects.filter(action='auth.blocked').count(),1)
