from datetime import timedelta
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from apps.analytics.models import AccessLog,ContentView,SecurityAlert
from apps.audit.models import AuditEvent
from apps.settings_app.models import GlobalSettings


class Command(BaseCommand):
    help='Retención controlada: simula por defecto; aplicar exige actor Superadmin y confirmación de días.'
    def add_arguments(self,parser):
        parser.add_argument('--apply',action='store_true')
        parser.add_argument('--authorized-by',type=int)
        parser.add_argument('--confirm-days',type=int)
    @transaction.atomic
    def handle(self,*args,**options):
        days=GlobalSettings.current().retention_days;cutoff=timezone.now()-timedelta(days=days)
        models=[ContentView,AccessLog,SecurityAlert,AuditEvent]
        groups=[model.objects.filter(created_at__lt=cutoff) for model in models]
        counts={model._meta.label:qs.count() for model,qs in zip(models,groups)}
        self.stdout.write(f'Política: {days} días. Candidatos: {counts}')
        if not options['apply']:
            self.stdout.write('SIMULACIÓN: no se elimina ningún dato.');return
        actor=User.objects.filter(pk=options['authorized_by'],is_active=True,authorized=True,role__code='superadmin').first()
        if not actor or options['confirm_days']!=days:
            raise CommandError('Aplicar requiere --authorized-by Superadmin activo y --confirm-days igual a la política vigente.')
        for qs in groups:qs.delete()
        AuditEvent.objects.create(actor=actor,entity='retention',action='retention.applied',metadata={'retention_days':days,'counts':counts})
        self.stdout.write('Retención aplicada; la operación quedó auditada.')
