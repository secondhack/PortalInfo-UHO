from django.core.management.base import BaseCommand
from apps.notifications.models import MailDelivery
from apps.notifications.services import send_delivery


class Command(BaseCommand):
    help='Reintenta la salida de correo pendiente/fallida; la demo solo usa archivo/consola.'
    def add_arguments(self,parser):parser.add_argument('--limit',type=int,default=100)
    def handle(self,*args,**options):
        ids=list(MailDelivery.objects.exclude(state='sent').order_by('id').values_list('pk',flat=True)[:max(1,min(options['limit'],1000))])
        sent=sum(send_delivery(pk) for pk in ids)
        self.stdout.write(f'Procesados: {len(ids)}; enviados al proveedor configurado: {sent}.')
