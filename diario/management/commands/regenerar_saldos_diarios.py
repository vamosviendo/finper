from django.core.management import BaseCommand

from diario.models import SaldoDiario, Cuenta, Movimiento


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for cuenta in Cuenta.todes():
            cuenta.recalcular_saldos_diarios()
