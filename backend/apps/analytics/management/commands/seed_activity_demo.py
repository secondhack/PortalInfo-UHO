from datetime import datetime,timedelta,timezone as dt_timezone
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from apps.approvals.models import Approval
from apps.content.models import Content,Submission,Response
from apps.content.queries import visible_publications
from apps.content.services import snapshot
from apps.notifications import services as notifications
from apps.settings_app.models import GlobalSettings
from apps.analytics.models import AccessLog,ContentView
from apps.analytics.periods import period_from
from apps.analytics.security import detect_alerts


class Command(BaseCommand):
    help='Actividad ficticia marcada DEMO, idempotente; no modifica datos manuales ni preferencias.'
    @transaction.atomic
    def handle(self,*args,**options):
        if settings.PRODUCTION or settings.AUTH_PROVIDER!='demo':raise CommandError('Solo permitido en demo local.')
        author=User.objects.filter(demo=True,email='demo.gestor@uho.edu.cu').first()
        admin=User.objects.filter(demo=True,email='demo.admin@uho.edu.cu').first()
        if not author or not admin:raise CommandError('Ejecute seed_demo antes de crear actividad DEMO.')
        cfg=GlobalSettings.current();seconds=cfg.security_window_minutes*60
        anchor=datetime.fromtimestamp(int((timezone.now()-timedelta(hours=2)).timestamp())//seconds*seconds,tz=dt_timezone.utc)
        for content in Content.objects.filter(seed_key__startswith='block2:',deleted_at__isnull=True).select_related('category','live_publication'):
            for approval in content.approvals.all():
                if not approval.proposal and approval.version==content.revision:
                    approval.proposal=snapshot(content);approval.save(update_fields=['proposal'])
                if approval.state=='pending':notifications.submitted(approval,demo=True)
                elif approval.state=='rejected':notifications.decided(approval,demo=True)
            if content.state=='approved' and content.live_publication_id:
                decision,created=Approval.objects.get_or_create(content=content,version=content.revision,state='approved',defaults={
                    'requested_by':author,'reviewer':admin,'reviewed_at':content.live_publication.created_at,'proposal':content.live_publication.data})
                if created:notifications.decided(decision,demo=True)
        for index in range(min(max(cfg.security_activity_threshold+1,6),50)+1):
            key=f'b3:access:{index}'
            when=anchor-timedelta(minutes=1) if index==0 else anchor+timedelta(seconds=index)
            log,created=AccessLog.objects.get_or_create(seed_key=key,defaults={'uid':'DEMO-seed-account','user_type':'demo','event_type':'access',
                'ip':f'192.0.2.{index%4+1}','user_agent':f'Windows DEMO device {index%4}','device':'desktop','section':'login','demo':True})
            if created:AccessLog.objects.filter(pk=log.pk).update(created_at=when)
        for index,user_type in enumerate(['institucional','trabajadores','estudiantes']):
            log,created=AccessLog.objects.get_or_create(seed_key=f'b3:type:{index}',defaults={'uid':f'DEMO-type-{index}',
                'user_type':user_type,'event_type':'access','ip':f'198.51.100.{index+1}','user_agent':'Android DEMO','device':'mobile','section':'login','demo':True})
            if created:AccessLog.objects.filter(pk=log.pk).update(created_at=anchor+timedelta(minutes=2))
        for publication in visible_publications().filter(content__seed_key__endswith=':approved'):
            key=f'b3:view:{publication.pk}'
            log,created=AccessLog.objects.get_or_create(seed_key=key,defaults={'uid':'DEMO-viewer','user_type':'demo','event_type':'view',
                'ip':'203.0.113.1','user_agent':'iPhone DEMO','device':'mobile','section':publication.category.slug,'content':publication.content,'demo':True})
            view,new=ContentView.objects.get_or_create(seed_key=key,defaults={'access_log':log,'category':publication.category,'content':publication.content,
                'uid':log.uid,'user_type':'demo','section':publication.category.slug,'ip':log.ip,'device':log.device,'demo':True})
            if created:AccessLog.objects.filter(pk=log.pk).update(created_at=anchor)
            if new:ContentView.objects.filter(pk=view.pk).update(created_at=anchor)
            if publication.data.get('type')=='survey' and not publication.data['details'].get('external_url'):
                for index in range(2):
                    submission,new=Submission.objects.get_or_create(seed_key=f'b3:vote:{publication.pk}:{index}',defaults={
                        'publication':publication,'respondent_key':f'DEMO-participant-{index}','demo':True})
                    if not new:continue
                    for q in publication.data['details'].get('questions',[]):
                        response=Response.objects.create(submission=submission,question_id=q['id'],respondent_key=submission.respondent_key,
                            value=f'Respuesta abierta DEMO {index+1}' if q['kind']=='open' else '')
                        options=[o['id'] for o in q['options']]
                        if q['kind']=='single':response.options.set(options[index%len(options):index%len(options)+1])
                        elif q['kind']=='multiple':response.options.set(options[:index+1])
        alerts=detect_alerts(period_from({'period':'7d','data_scope':'demo'}))
        self.stdout.write(f'Actividad semilla DEMO preparada. Alertas nuevas: {alerts}. La fuente predeterminada de métricas la excluye.')
