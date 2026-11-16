import json
import secrets
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Crea visitantes ficticios sin permisos CMS; conserva las credenciales existentes.'

    def handle(self, *args, **options):
        if settings.PRODUCTION or settings.PORTAL_AUTH_MODE != 'demo':
            raise CommandError('La semilla de visitantes solo se permite en demostración.')
        target = settings.PORTAL_DEMO_USERS_FILE
        if target.exists():
            self.stdout.write('Visitantes existentes conservados; no se regeneraron contraseñas.')
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        users = {}
        credentials = ['CUENTAS FICTICIAS DEL PORTAL; no conceden acceso a Internet ni al CMS.']
        for suffix, name, kind in [('estudiante', 'Estudiante de demostración', 'estudiantes'),
                ('trabajador', 'Trabajadora de demostración', 'trabajadores'),
                ('institucional', 'Visitante de demostración', 'institucional')]:
            username = 'demo.' + suffix
            password = secrets.token_urlsafe(18)
            users[username] = {'full_name': name, 'user_type': kind, 'active': True, 'password_hash': make_password(password)}
            credentials.append(f'{username}: {password}')
        with target.open('x', encoding='utf-8') as output:
            json.dump(users, output, ensure_ascii=False, indent=2)
        private = target.with_name('portal-demo-credentials.txt')
        with private.open('x', encoding='utf-8') as output:
            output.write('\n'.join(credentials) + '\n')
        self.stdout.write('Visitantes creados. Credenciales privadas en .local/portal-demo-credentials.txt; no compartirlas.')
