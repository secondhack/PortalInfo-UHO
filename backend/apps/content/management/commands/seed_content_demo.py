from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from apps.approvals.models import Approval
from apps.catalogs.models import Category,CatalogItem
from apps.settings_app.models import GlobalSettings
from apps.content.models import Content,News,Event,Service,Survey,Question,Option
from apps.content.services import publish


class Command(BaseCommand):
    help='Añade ejemplos ficticios de contenidos; no modifica registros existentes ni crea respuestas.'
    @transaction.atomic
    def handle(self,*args,**kwargs):
        if settings.PRODUCTION or settings.AUTH_PROVIDER!='demo': raise CommandError('Solo disponible en demo local.')
        author=User.objects.filter(email='demo.gestor@uho.edu.cu',demo=True).first()
        admin=User.objects.filter(email='demo.admin@uho.edu.cu',demo=True).first()
        if not author or not admin: raise CommandError('Ejecute seed_demo para inicializar las identidades.')
        area=CatalogItem.objects.filter(catalog__slug='areas',name__startswith='Ejemplo DEMO').first()
        if not area: raise CommandError('Falta el área de ejemplo; ejecute seed_demo.')
        dynamic,_=Category.objects.get_or_create(slug='demo-logros',defaults={'name':'Logros DEMO','dynamic':True})
        cfg=GlobalSettings.current(); count=0
        for cat in list(Category.objects.filter(dynamic=False))+[dynamic]:
            for state in ['draft','pending','approved','rejected','hidden','expired','future']:
                key=f'block2:{cat.pk}:{state}'
                if Content.objects.filter(seed_key=key).exists(): continue
                now=timezone.now(); starts=now-timedelta(hours=1); ends=now+timedelta(days=3)
                if state=='expired': starts=now-timedelta(days=5); ends=now-timedelta(days=1)
                if state=='future': starts=now+timedelta(days=1); ends=now+timedelta(days=2)
                editorial='approved' if state in ('expired','future') else state
                item=Content.objects.create(seed_key=key,category=cat,author=author,title=f'DEMO · {cat.name} · {state}'[:cat.title_limit],
                    description='Ejemplo ficticio para la demostración.'[:cat.description_limit],state=editorial,
                    validity='custom',starts_at=starts,ends_at=ends,manual_active=state!='hidden',
                    extra_fields={field:'Ejemplo DEMO' for field in cat.required_fields})
                if cat.content_type=='news': News.objects.create(content=item,area=area,external_url='https://example.invalid/noticia')
                if cat.content_type=='event': Event.objects.create(content=item,area=area,event_at=now+timedelta(days=2),contact='Contacto ficticio DEMO')
                if cat.content_type=='service': Service.objects.create(content=item,area=area,access_url='https://example.invalid/servicio')
                if cat.content_type=='survey':
                    survey=Survey.objects.create(content=item)
                    kinds=['single','multiple','open'] if cfg.allow_open_questions else ['single','multiple']
                    for position,kind in enumerate(kinds[:cfg.max_questions]):
                        q=Question.objects.create(survey=survey,text=f'Pregunta ficticia DEMO ({kind})',kind=kind,position=position)
                        if kind!='open': Option.objects.bulk_create([Option(question=q,text='Opción A'),Option(question=q,text='Opción B')])
                if editorial=='approved': publish(item,admin)
                if editorial in ('pending','rejected'):
                    Approval.objects.create(content=item,requested_by=author,reviewer=admin if editorial=='rejected' else None,
                        state=editorial,reason='Ejemplo ficticio de rechazo.' if editorial=='rejected' else '')
                    item.submitted_at=now; item.save(update_fields=['submitted_at'])
                count+=1
        self.stdout.write(f'Contenidos DEMO nuevos: {count}. No se crearon respuestas simuladas.')
