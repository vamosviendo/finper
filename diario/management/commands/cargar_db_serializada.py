from __future__ import annotations

import datetime
import json
from pathlib import Path

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, call_command

from diario.models import Titular, Moneda, Cuenta, Movimiento, CuentaInteractiva
from diario.serializers import CuentaSerializada, MovimientoSerializado
from finper import settings
from vvmodel.models import MiModel
from vvmodel.serializers import SerializedDb, SerializedObject


def _cargar_modelo_simple(modelo: str, de_serie: SerializedDb, excluir_campos: list[str] = None) -> None:
    """ Carga modelos que no incluyan foreignfields, polimorfismo u otras complicaciones"""
    excluir_campos = excluir_campos or []
    serie_modelo = de_serie.filter_by_model(modelo)
    Modelo: type | MiModel = apps.get_model(*modelo.split("."))

    for elemento in serie_modelo:
        fields = {k: v for k, v in elemento.fields.items() if k not in excluir_campos}
        Modelo.crear(**fields)


def _cargar_cuentas_y_movimientos(de_serie: SerializedDb) -> None:
    cuentas = CuentaSerializada.todes(container=de_serie)
    cuentas_independientes = SerializedDb([
        x for x in cuentas.filtrar(cta_madre=None) if not x.es_cuenta_credito()
    ])
    cuentas_acumulativas = cuentas.filter_by_model("diario.cuentaacumulativa")
    movimientos = MovimientoSerializado.todes(container=de_serie)

    for cuenta in cuentas_independientes:

        # Intentar crear la cuenta. Si la cuenta ya fue creada
        # (como contracuenta de un crédito, por ejemplo?), tomarla.
        try:
            cuenta_ok = Cuenta.crear(
                nombre=cuenta.fields["nombre"],
                slug=cuenta.fields["slug"],
                cta_madre=None,
                fecha_creacion=cuenta.fields["fecha_creacion"],
                titular=Titular.tomar(titname=cuenta.titname()),
                moneda=Moneda.tomar(monname=cuenta.fields["moneda"][0]),
            )
        except ValidationError:
            cuenta_ok = Cuenta.tomar(slug=cuenta.fields["slug"])

        # Si la cuenta recién creada es (en la db serializada) una cuenta acumulativa:
        if cuenta.pk in [x.pk for x in cuentas_acumulativas]:
            # Buscar posibles movimientos en los que haya intervenido la cuenta
            # antes de convertirse en acumulativa
            movimientos_cuenta = SerializedDb([
                x for x in movimientos
                if x.fields['cta_entrada'] == [cuenta.fields['slug']]
                or x.fields['cta_salida'] == [cuenta.fields['slug']]
            ])

            # Retirar de serie movimientos los movimientos de la cuenta acumulativa
            # TODO: Por claridad, si es inocuo, estaría bien que esto sucediera al final del procesamiento
            #       de la cuenta.
            movimientos = SerializedDb([x for x in movimientos if x not in movimientos_cuenta])

            # En este complicado movimiento que tendré que tratar de simplificar luego hago lo siguiente:
            #
            # Recorro los movimientos en los que interviene la cuenta, verificando que la cuenta de entrada
            # y la cuenta de salida, en caso de tenerlas, existan. Si es el caso, las guardaremos en
            # sendas variables.
            # En caso de que alguna de las dos cuentas no exista, damos por sentado (veremos luego si con razón o no)
            # que la cuenta que todavía no se recreó era una subcuenta de la cuenta que ocupa el lugar opuesto.
            # Damos por sentado también que el movimiento es un movimiento de traspaso, es decir que la cuenta
            # opuesta no es None, y que es una cuenta existente.
            # Damos por sentado, finalmente, que el movimiento que es un movimiento de traspaso es el movimiento
            # de traspaso de saldo que corresponde a la creación de la subcuenta al momento de la división de una
            # cuenta con saldo. (1)
            # Dando todas estas cosas por sentadas, señalamos la posición de la cuenta receptora de saldo como
            # cuenta de entrada o de salida en el movimiento, y guardamos el movimiento en una lista de traspasos
            # de saldo, que usaremos luego para la división de la cuenta.
            # (1) Habría que ver si todas estas cosas que se dan por sentadas no deberían ser chequeadas y lanzar
            # una excepción en el caso de que alguna de ellas no se cumpla (es decir, en el caso de que la otra
            # cuenta del movimiento sea None, en el caso de que no sea None pero no exista en la base de datos,
            # en el caso de que no esté indicada en la base de datos serializada como cuenta madre de la cuenta
            # inexistente o en el caso (si es que es posible testear esto) de que el movimiento no constituya un
            # traspaso de saldo entre una cuenta que se convierte en acumulativa y una de sus subcuentas (que sea,
            # por ejemplo, un movimiento entre una cuenta interactiva cualquiera y una subcuenta que todavía no
            # existe pero que pertenece a otra cuenta)
            # De todos modos, si damos por sentado esto es porque la cuenta está marcada como acumulativa. Hay que
            # ver si hacemos bien (el último ejemplo es el que más me preocupa)
            traspasos_de_saldo = SerializedDb()
            ambas_cuentas_existen = True
            for movimiento in movimientos_cuenta:
                try:
                    ce = CuentaInteractiva.tomar(
                        slug=movimiento.fields['cta_entrada'][0]
                    ) if movimiento.fields['cta_entrada'] is not None else None
                except CuentaInteractiva.DoesNotExist:
                    ambas_cuentas_existen = False
                    movimiento.pos_cta_receptora = "cta_entrada"
                    traspasos_de_saldo.append(movimiento)

                try:
                    cs = CuentaInteractiva.tomar(
                        slug=movimiento.fields['cta_salida'][0]
                    ) if movimiento.fields['cta_salida'] is not None else None
                except CuentaInteractiva.DoesNotExist:
                    ambas_cuentas_existen = False
                    movimiento.pos_cta_receptora = "cta_salida"
                    traspasos_de_saldo.append(movimiento)

                # En caso de que no haya una cuenta aún no existente en la base de datos entre las cuentas
                # intervinientes en el movimiento, se supone que el movimiento se produjo antes que la cuenta
                # se convirtiera en acumulativa y se lo genera a partir de los datos del objeto serializado
                # correspondiente.
                if ambas_cuentas_existen:
                    Movimiento.crear(
                        fecha=movimiento.fields['dia'][0],
                        orden_dia=movimiento.fields['orden_dia'],
                        concepto=movimiento.fields['concepto'],
                        importe=movimiento.fields['_importe'],
                        cta_entrada=ce,
                        cta_salida=cs,
                        moneda=Moneda.tomar(
                            monname=movimiento.fields['moneda'][0]
                        ),
                        id_contramov=movimiento.fields['id_contramov'],
                        es_automatico=movimiento.fields['es_automatico'],
                        esgratis=movimiento.fields['id_contramov'] is None,
                    )

            # Una vez terminados de recorrer los movimientos de la cuenta y ya
            # generados los movimientos anteriores a su conversión, se procede
            # a la división de la cuenta en subcuentas y su conversión en acumulativa.
            # Si hay movimientos marcados como traspasos de saldo, los usamos para
            # tomar el dato del saldo traspasado desde la cuenta acumulativa
            # a sus subcuentas al momento de la conversión.
            slugs_subcuentas_con_saldo = [mov.fields[mov.pos_cta_receptora][0] for mov in traspasos_de_saldo]

            # Buscar las subcuentas en las que está dividida
            subcuentas_cuenta = cuentas.filtrar(cta_madre=[cuenta.fields["slug"]])

            # De las subcuentas encontradas, usar aquellas cuya fecha de creación
            # coincide con la fecha de conversión de la cuenta en acumulativa
            # para dividir y convertir la cuenta.
            fecha_conversion = cuenta.campos_polimorficos()["fecha_conversion"]

            subcuentas_fecha_conversion = []
            for subc in subcuentas_cuenta.filtrar(fecha_creacion=fecha_conversion):
                slug_subc = subc.fields["slug"]
                if slug_subc in slugs_subcuentas_con_saldo:
                    mov = traspasos_de_saldo[slugs_subcuentas_con_saldo.index(slug_subc)]
                    saldo = traspasos_de_saldo.tomar(**{mov.pos_cta_receptora: [slug_subc]}).fields["_importe"]
                    if mov.pos_cta_receptora == "cta_salida":
                        saldo = -saldo
                else:
                    saldo = 0

                subcuentas_fecha_conversion.append({
                    "nombre": subc.fields["nombre"],
                    "slug": subc.fields["slug"],
                    "titular": Titular.tomar(titname=subc.titname()),
                    "saldo": saldo
                })

            cuenta_ok = cuenta_ok.dividir_y_actualizar(
                *subcuentas_fecha_conversion,
                fecha=datetime.date(*[int(x) for x in fecha_conversion.split("-")])
            )

            # Se agregan las subcuentas cuya fecha de creación es posterior
            # a la fecha de conversión de la cuenta en acumulativa
            # (creadas mediante el método CuentaAcumulativa.agregar_subcuenta)
            subcuentas_posteriores = [[
                    x.fields["nombre"],
                    x.fields["slug"],
                    Titular.tomar(titname=x.titname()),
                    x.fields["fecha_creacion"]
                ]
                for x in subcuentas_cuenta
                if x.fields["fecha_creacion"] > fecha_conversion
            ]
            for subcuenta in subcuentas_posteriores:
                cuenta_ok.agregar_subcuenta(*subcuenta)

    for movimiento in movimientos.filtrar(es_automatico=False):
        ce = CuentaInteractiva.tomar(
            slug=movimiento.fields['cta_entrada'][0]
        ) if movimiento.fields['cta_entrada'] is not None else None
        cs = CuentaInteractiva.tomar(
            slug=movimiento.fields['cta_salida'][0]
        ) if movimiento.fields['cta_salida'] is not None else None

        Movimiento.crear(
            fecha=movimiento.fields['dia'][0],
            orden_dia=movimiento.fields['orden_dia'],
            concepto=movimiento.fields['concepto'],
            importe=movimiento.fields['_importe'],
            cta_entrada=ce,
            cta_salida=cs,
            moneda=Moneda.tomar(
                monname=movimiento.fields['moneda'][0]
            ),
            id_contramov=movimiento.fields['id_contramov'],
            es_automatico=movimiento.fields['es_automatico'],
            esgratis=movimiento.fields['id_contramov'] is None,
        )


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Path(settings.BASE_DIR / "db.sqlite3").unlink(missing_ok=True)
        call_command("migrate")

        with open("db_full.json", "r") as db_full_json:
            db_full = SerializedDb([
                SerializedObject(x) for x in json.load(db_full_json)
            ])

        _cargar_modelo_simple("diario.titular", db_full, ["deudores"])
        _cargar_modelo_simple("diario.moneda", db_full)
        _cargar_cuentas_y_movimientos(db_full)
        # _cargar_movimientos(db_full)
        #
        # for x in [x for x in db_full if x.model == "diario.movimiento"]:
        #     x.fields.update({"importe": x.fields.pop("_importe")})
        # _cargar_modelo("diario.movimiento", db_full)
