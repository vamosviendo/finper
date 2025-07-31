from django.core.management import BaseCommand

from diario.models import Cuenta


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("origen", nargs="+", type=str)
        parser.add_argument("destino", nargs="+", type=str)

    def handle(self, *args, **options):
        cuenta_origen = Cuenta.tomar(sk=options["origen"][0])
        cuenta_destino = Cuenta.tomar(sk=options["destino"][0])
        movs_origen = cuenta_origen.movs()
        for mov in movs_origen:
            print(
                f"Pasando mov {mov.pk}: {mov.orden_dia} del {mov.fecha} - "
                f"de {cuenta_origen.nombre} a {cuenta_destino.nombre}", end="")
            if mov.cta_entrada == cuenta_origen:
                mov.cta_entrada = cuenta_destino
            elif mov.cta_salida == cuenta_origen:
                mov.cta_salida = cuenta_destino
            mov.clean_save()
            print(" - OK")
