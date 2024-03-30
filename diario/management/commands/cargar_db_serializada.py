import json
from pathlib import Path

from django.core.management import BaseCommand, call_command

from diario.models import Titular, Moneda
from finper import settings
from vvmodel.serializers import SerializedDb, SerializedObject


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Path(settings.BASE_DIR / "db.sqlite3").unlink(missing_ok=True)
        call_command("migrate")

        with open("db_full.json", "r") as db_full_json:
            db_full = SerializedDb([
                SerializedObject(x) for x in json.load(db_full_json)
            ])

        titulares = db_full.filter_by_model("diario.titular")
        monedas = db_full.filter_by_model("diario.moneda")

        for titular in titulares:
            Titular.crear(
                nombre=titular.fields["nombre"],
                titname=titular.fields["titname"],
                fecha_alta=titular.fields["fecha_alta"],
            )

        for moneda in monedas:
            Moneda.crear(**moneda.fields)

        #
        # try:
        #     call_command("loaddata", "db_full.json")
        # except ValueError:
        #     pass
