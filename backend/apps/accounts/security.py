from functools import lru_cache
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.utils.crypto import salted_hmac


@lru_cache(maxsize=1)
def dummy_password_hash():
    return make_password('timing-padding-only-not-a-credential')


def lock_login_ip(ip, namespace):
    """Caller holds transaction.atomic; coordinate failed-attempt budgets across workers."""
    key = int(salted_hmac(namespace+'-login-lock', ip).hexdigest()[:15], 16)
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_xact_lock(%s)', [key])
