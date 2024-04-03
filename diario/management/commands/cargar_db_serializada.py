import datetime
import json
from pathlib import Path

from django.core.management import BaseCommand, call_command

from diario.models import Titular, Moneda, Cuenta, CuentaAcumulativa
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
        for titular in titulares:
            Titular.crear(
                nombre=titular.fields["nombre"],
                titname=titular.fields["titname"],
                fecha_alta=titular.fields["fecha_alta"],
            )

        monedas = db_full.filter_by_model("diario.moneda")
        for moneda in monedas:
            Moneda.crear(**moneda.fields)

        cuentas = db_full.filter_by_model("diario.cuenta")
        cuentas_independientes = SerializedDb([x for x in cuentas if x.fields["cta_madre"] is None])
        cuentas_acumulativas = db_full.filter_by_model("diario.cuentaacumulativa")
        for cuenta in cuentas_independientes:
            try:
                titname = db_full.primere(
                    "diario.cuentainteractiva", pk=cuenta.pk
                ).fields["titular"][0]
            except AttributeError:
                titname = db_full.primere(
                    "diario.cuentaacumulativa", pk=cuenta.pk
                ).fields["titular_original"][0]

            cuenta_ok = Cuenta.crear(
                nombre=cuenta.fields["nombre"],
                slug=cuenta.fields["slug"],
                cta_madre=None,
                fecha_creacion=cuenta.fields["fecha_creacion"],
                titular=Titular.tomar(titname=titname),
                moneda=Moneda.tomar(monname=cuenta.fields["moneda"][0]),
            )

            if cuenta.pk in [x.pk for x in cuentas_acumulativas]:
                subcuentas_cuenta = [
                    [x.fields["nombre"], x.fields["slug"], 0]
                    for x in cuentas
                    if x.fields["cta_madre"] == [cuenta.fields["slug"]]
                ]
                fecha_conversion = cuentas_acumulativas.primere(
                    "diario.cuentaacumulativa",
                    pk=cuenta.pk
                ).fields["fecha_conversion"]

                cuenta_ok.dividir_entre(
                    *subcuentas_cuenta,
                    fecha=datetime.date(*[int(x) for x in fecha_conversion.split("-")])
                )

        #
        # try:
        #     call_command("loaddata", "db_full.json")
        # except ValueError:
        #     pass
