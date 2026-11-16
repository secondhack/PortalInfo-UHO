from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from apps.accounts.models import User
from apps.settings_app.models import GlobalSettings
from .models import Notification,MailDelivery


@transaction.atomic
def send_delivery(pk):
    delivery=MailDelivery.objects.select_for_update().select_related('notification__recipient').get(pk=pk)
    if delivery.state=='sent': return False
    notification=delivery.notification
    delivery.attempts+=1
    try:
        context={'notification':notification,'path':f'/contents?content={notification.resource_id}' if notification.resource_id else '/notifications'}
        text=render_to_string('notifications/event.txt',context)
        mail=EmailMultiAlternatives(notification.title or 'PortalInfo UHO',text,to=[notification.recipient.email])
        mail.attach_alternative(render_to_string('notifications/event.html',context),'text/html')
        mail.send(fail_silently=False)
        delivery.state='sent';delivery.sent_at=timezone.now();delivery.error_code=''
    except Exception as error:
        # Never persist server credentials, message contents or raw SMTP exceptions.
        delivery.state='failed';delivery.error_code=type(error).__name__[:100]
    delivery.save(update_fields=['state','attempts','error_code','sent_at'])
    return delivery.state=='sent'


def notify(recipient,kind,title,message,event_key,resource_id=None,demo=False):
    notification,created=Notification.objects.get_or_create(recipient=recipient,event_key=event_key,
        defaults={'kind':kind,'title':title,'message':message,'resource_type':'content' if resource_id else '',
            'resource_id':resource_id,'demo':demo})
    if created and GlobalSettings.current().email_notifications and recipient.is_active and recipient.authorized:
        delivery=MailDelivery.objects.create(notification=notification)
        transaction.on_commit(lambda pk=delivery.pk:send_delivery(pk))
    return notification


def submitted(approval,demo=False):
    for admin in User.objects.filter(is_active=True,authorized=True,role__code__in=['admin','superadmin']):
        notify(admin,'content.submitted','Contenido pendiente de aprobación',
            f'La revisión {approval.version} de «{approval.content.title}» solicita publicación.',
            f'approval:{approval.pk}:pending',approval.content_id,demo)


def decided(approval,demo=False):
    approved=approval.state=='approved'
    notify(approval.content.author,'content.approved' if approved else 'content.rejected',
        'Contenido aprobado' if approved else 'Contenido rechazado',
        f'La revisión {approval.version} de «{approval.content.title}» fue '+('aprobada.' if approved else f'rechazada. Motivo: {approval.reason}'),
        f'approval:{approval.pk}:{approval.state}',approval.content_id,demo)


def expired(publication,demo=False):
    return notify(publication.content.author,'content.expired','Publicación vencida',
        f'La versión {publication.version} de «{publication.data.get("title","")}» terminó su vigencia.',
        f'publication:{publication.pk}:expired',publication.content_id,demo)
