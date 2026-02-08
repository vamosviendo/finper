from datetime import datetime

from django.core.management import BaseCommand

from diario.models import Cuenta, Dia


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--cuenta",
            type=str,
            help="SK de la cuenta para la cual regenerar saldos diarios. "
                 "Si se omite, se procesan todas las cuentas-"
        )
        parser.add_argument(
            "--desde",
            type=str,
            help="Fecha desde la cual recalcular. "
                 "Si no se especifica, se recalcula desde el inicio."
        )

    def handle(self, *args, **kwargs):
        cuenta_sk = kwargs.get("cuenta")
        desde_str = kwargs.get("desde")

        if cuenta_sk:
            cuentas = Cuenta.filtro(sk=cuenta_sk)
            if not cuentas.exists():
                raise ValueError(f"SK {cuenta_sk} no existe")
        else:
            cuentas = Cuenta.todes()

        try:
            desde = datetime.strptime(desde_str, "%Y-%m-%d").date() if desde_str else None
        except ValueError:
            raise ValueError("Fecha mal formateiada. Debe ser YYYY-MM-DD")
        dia = Dia.filtro(fecha__gte=desde).first() if desde else None

        for cuenta in cuentas:
            cuenta.recalcular_saldos_diarios(desde=dia)
