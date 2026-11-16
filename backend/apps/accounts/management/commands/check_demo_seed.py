"""A non-destructive runtime verification of seed idempotency."""
from django.core.management import BaseCommand, call_command
from apps.accounts.models import User
from apps.catalogs.models import Category, CatalogItem


class Command(BaseCommand):
    help = 'Comprueba que repetir seed_demo conserva usuarios, hashes y datos de catálogo.'

    def handle(self, *args, **kwargs):
        def snapshot():
            return (list(User.objects.order_by('pk').values_list('pk','email','password','role_id','is_active')),
                list(Category.objects.order_by('pk').values()), list(CatalogItem.objects.order_by('pk').values()))
        before = snapshot()
        call_command('seed_demo')
        if before != snapshot():
            from django.core.management.base import CommandError
            raise CommandError('La inicialización añadió datos pendientes. Repita después de inicializar.')
        self.stdout.write(self.style.SUCCESS('Idempotencia comprobada: usuarios, hashes y catálogos conservados.'))
