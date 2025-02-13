from io import StringIO

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        serialized_db = StringIO()
        call_command(
            'dumpdata',
            'diario.moneda',
            'diario.cotizacion',
            'diario.titular',
            'diario.cuenta',
            'diario.cuentaacumulativa',
            'diario.cuentainteractiva',
            'diario.dia',
            'diario.movimiento',
            'diario.saldo',
            '--natural-foreign',
            indent=2,
            stdout=serialized_db
        )

        with open('db_full.json', 'w') as db_full:
            db_full.write(serialized_db.getvalue())
