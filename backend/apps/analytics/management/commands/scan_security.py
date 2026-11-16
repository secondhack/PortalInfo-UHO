from django.core.management.base import BaseCommand
from apps.analytics.periods import period_from
from apps.analytics.security import detect_alerts


class Command(BaseCommand):
    help='Genera señales defensivas configuradas, sin bloqueos automáticos.'
    def add_arguments(self,parser):
        parser.add_argument('--period',default='7d',choices=['today','7d','30d','month'])
        parser.add_argument('--data-scope',default='real',choices=['real','demo','all'])
    def handle(self,*args,**options):
        self.stdout.write(f'Alertas nuevas: {detect_alerts(period_from({"period":options["period"],"data_scope":options["data_scope"]}))}')
