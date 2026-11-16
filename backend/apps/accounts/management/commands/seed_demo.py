import os
import secrets
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.accounts.models import User, Role, Grant
from apps.catalogs.models import Category, CatalogType, CatalogItem
from apps.settings_app.models import GlobalSettings


class Command(BaseCommand):
    help = 'Inicializa identidades ficticias sin sobrescribir registros existentes.'

    def add_arguments(self,parser):parser.add_argument('--with-activity',action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        if settings.PRODUCTION or settings.AUTH_PROVIDER != 'demo':
            raise CommandError('Datos demo permitidos únicamente en desarrollo con AUTH_PROVIDER=demo.')
        roles = {code: Role.objects.get_or_create(code=code, defaults={'name': label})[0] for code,label in Role.Code.choices}
        categories = []
        content_types={'noticias':'news','eventos':'event','avisos':'notice','servicios':'service','encuestas':'survey'}
        for slug, name, visible, title, description in [('noticias','Noticias',5,100,300),('eventos','Eventos',4,120,400),('avisos','Avisos',3,80,250),('servicios','Servicios RedUHO',8,60,150),('encuestas','Encuestas',1,150,200)]:
            category,_ = Category.objects.get_or_create(slug=slug, defaults={'name':name,'dynamic':False,'content_type':content_types[slug],'max_visible':visible,'title_limit':title,'description_limit':description})
            categories.append(category)
            for operation,_ in Grant.Operation.choices:
                Grant.objects.get_or_create(role=roles['gestor'],category=category,operation=operation)
        for slug,name in [('areas','Áreas'),('departamentos','Departamentos'),('tipos-servicio','Tipos de servicio'),('cargos','Cargos'),('carreras','Carreras')]:
            catalog,_ = CatalogType.objects.get_or_create(slug=slug,defaults={'name':name})
            CatalogItem.objects.get_or_create(catalog=catalog,name=f'Ejemplo DEMO · {name}',defaults={'description':'Dato ficticio de demostración.'})
        created_credentials = []
        for code in roles:
            email = f'demo.{code}@uho.edu.cu'
            if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                continue
            password = os.getenv(f'DEMO_{code.upper()}_PASSWORD') or secrets.token_urlsafe(20)
            user = User(email=email,username=email,role=roles[code],demo=True,protected=code=='superadmin',is_staff=code=='superadmin')
            user.set_password(password)
            user.save()
            if code == 'gestor':
                user.categories.set(categories[:2])
            created_credentials.append(f'{email}\t{password}')
        GlobalSettings.current()
        if created_credentials:
            local = settings.BASE_DIR.parent / '.local'
            local.mkdir(exist_ok=True)
            with (local/'demo-credentials.txt').open('a',encoding='utf-8') as handle:
                handle.write('\n'.join(created_credentials)+'\n')
        self.stdout.write(self.style.SUCCESS('Inicialización completada. Credenciales nuevas en .local/demo-credentials.txt (archivo privado, no versionado).'))
        from django.core.management import call_command
        call_command('seed_content_demo')
        if options.get('with_activity'):call_command('seed_activity_demo')
