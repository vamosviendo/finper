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

        cuentas = Cuenta.filtro(sk=cuenta_sk) if cuenta_sk else Cuenta.todes()
        desde = datetime.strptime(desde_str, "%Y-%m-%d").date() if desde_str else None
        dia = Dia.tomar(fecha=desde) if desde else None
        print("cuentas", *[c.sk for c in Cuenta.todes()])

        for cuenta in cuentas:
            cuenta.recalcular_saldos_diarios(desde=dia)
