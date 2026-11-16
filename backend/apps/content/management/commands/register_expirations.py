from django.core.management.base import BaseCommand
from apps.content.services import register_expirations


class Command(BaseCommand):
    help='Registra expiraciones una sola vez; la API ya oculta lo vencido sin depender del comando.'
    def handle(self,*args,**kwargs):
        self.stdout.write(f'Expiraciones nuevas: {register_expirations()}')
