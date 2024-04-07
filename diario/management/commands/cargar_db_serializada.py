from __future__ import annotations

import datetime
import json
from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, call_command

from diario.models import Titular, Moneda, Cuenta
from finper import settings
from vvmodel.models import MiModel
from vvmodel.serializers import SerializedDb, SerializedObject


def _cargar_modelo(modelo: str, de_serie: SerializedDb, excluir_campos: list[str] = None) -> None:
    excluir_campos = excluir_campos or []
    serie_modelo = de_serie.filter_by_model(modelo)
    Modelo: type | MiModel = apps.get_model(*modelo.split("."))

    for elemento in serie_modelo:
        fields = {k: v for k, v in elemento.fields.items() if k not in excluir_campos}
        Modelo.crear(**fields)


def _cargar_cuentas(de_serie: SerializedDb) -> None:
    cuentas = de_serie.filter_by_model("diario.cuenta")
    cuentas_independientes = cuentas.filtrar(cta_madre=None)
    cuentas_acumulativas = de_serie.filter_by_model("diario.cuentaacumulativa")
    cuentas_interactivas = de_serie.filter_by_model("diario.cuentainteractiva")

    for cuenta in cuentas_independientes:
        try:
            titname = cuentas_interactivas.tomar(pk=cuenta.pk).fields["titular"]
        except StopIteration:
            titname = cuentas_acumulativas.tomar(pk=cuenta.pk).fields["titular_original"]

        cuenta_ok = Cuenta.crear(
            nombre=cuenta.fields["nombre"],
            slug=cuenta.fields["slug"],
            cta_madre=None,
            fecha_creacion=cuenta.fields["fecha_creacion"],
            titular=Titular.tomar(titname=titname[0]),
            moneda=Moneda.tomar(monname=cuenta.fields["moneda"][0]),
        )

        # Si la cuenta recién creada es (en la db serializada) una cuenta acumulativa:
        if cuenta.pk in [x.pk for x in cuentas_acumulativas]:
            # Buscar las subcuentas en las que está dividida
            subcuentas_cuenta = cuentas.filtrar(cta_madre=[cuenta.fields["slug"]])
            # De las subcuentas encontradas, usar aquellas cuya fecha de creación
            # coincide con la fecha de conversión de la cuenta en acumulativa
            # para dividir y convertir la cuenta.
            fecha_conversion = cuentas_acumulativas.tomar(pk=cuenta.pk).fields["fecha_conversion"]
            subcuentas_fecha_conversion = [
                {
                    "nombre": x.fields["nombre"],
                    "slug": x.fields["slug"],
                    "titular": Titular.tomar(titname=cuentas_interactivas.tomar(pk=x.pk).fields["titular"][0]),
                    "saldo": 0
                }
                for x in subcuentas_cuenta.filtrar(fecha_creacion=fecha_conversion)
            ]
            cuenta_ok = cuenta_ok.dividir_y_actualizar(
                *subcuentas_fecha_conversion,
                fecha=datetime.date(*[int(x) for x in fecha_conversion.split("-")])
            )

            # Se agregan las subcuentas cuya fecha de creación es posterior
            # a la fecha de conversión de la cuenta en acumulativa
            subcuentas_posteriores = [[
                    x.fields["nombre"],
                    x.fields["slug"],
                    Titular.tomar(titname=cuentas_interactivas.tomar(pk=x.pk).fields["titular"][0]),
                    x.fields["fecha_creacion"]
                ]
                for x in subcuentas_cuenta
                if x.fields["fecha_creacion"] != fecha_conversion
            ]
            for subcuenta in subcuentas_posteriores:
                cuenta_ok.agregar_subcuenta(*subcuenta)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Path(settings.BASE_DIR / "db.sqlite3").unlink(missing_ok=True)
        call_command("migrate")

        with open("db_full.json", "r") as db_full_json:
            db_full = SerializedDb([
                SerializedObject(x) for x in json.load(db_full_json)
            ])

        _cargar_modelo("diario.titular", db_full, ["deudores"])
        _cargar_modelo("diario.moneda", db_full)
        _cargar_cuentas(db_full)
