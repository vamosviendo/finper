from __future__ import annotations

import datetime
import json
from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, call_command

from diario.models import Titular, Moneda, Cotizacion, Cuenta, Movimiento, CuentaInteractiva
from diario.serializers import CuentaSerializada, MovimientoSerializado
from finper import settings
from utils.errors import ElementoSerializadoInexistente
from vvmodel.models import MiModel
from vvmodel.serializers import SerializedDb, SerializedObject


def _tomar_o_crear_cuenta(cuenta: CuentaSerializada | None) -> CuentaInteractiva | None:
    if cuenta:
        try:
            print(f"Tomando cuenta existente <{cuenta.fields['nombre']}>", end=" ")
            return CuentaInteractiva.tomar(slug=cuenta.fields["slug"])
        except CuentaInteractiva.DoesNotExist:
            print(f"Creando cuenta <{cuenta.fields['nombre']}>", end=" ")
            return Cuenta.crear(
                nombre=cuenta.fields["nombre"],
                slug=cuenta.fields["slug"],
                cta_madre=cuenta.fields["cta_madre"],
                fecha_creacion=cuenta.fields["fecha_creacion"],
                titular=Titular.tomar(titname=cuenta.titname()),
                moneda=Moneda.tomar(monname=cuenta.fields["moneda"][0]),
            )
        finally:
            print("- OK")

    return None


def _slug_cuenta_mov(
        movimiento: MovimientoSerializado,
        posicion: str,
        container_cuentas: SerializedDb[CuentaSerializada]) -> str:
    """ Toma un movimiento y devuelve el slug de la cuenta interviniente
        en la posición indicada. """
    if posicion not in ["entrada", "salida", "cta_entrada", "cta_salida"]:
        raise ValueError('Los valores aceptados para posicion son "entrada", "salida", "cta_entrada" o "cta_salida"')
    cta = movimiento.fields[posicion] if posicion.startswith("cta_") else f"cta_{posicion}"
    slug = cta[0] if cta else None
    # Si la cuenta del movimiento no existe como objeto serializado, lanzar excepción
    if slug and slug not in [x.fields["slug"] for x in container_cuentas.filter_by_model("diario.cuenta")]:
        raise ElementoSerializadoInexistente(modelo="diario.cuenta", identificador=slug)
    return slug


def _cuenta_mov(
        movimiento: MovimientoSerializado,
        posicion: str,
        container_cuentas: SerializedDb[CuentaSerializada]) -> CuentaInteractiva | None:
    if posicion not in ["entrada", "salida", "cta_entrada", "cta_salida"]:
        raise ValueError('Los valores aceptados para posicion son "entrada", "salida", "cta_entrada" o "cta_salida"')
    cta = movimiento.fields[posicion] if posicion.startswith("cta_") else f"cta_{posicion}"
    slug = movimiento.fields[posicion][0] if movimiento.fields[posicion] else None
    if slug:
        if slug not in [x.fields["slug"] for x in container_cuentas.filter_by_model("diario.cuenta")]:
            raise ElementoSerializadoInexistente(modelo="diario.cuenta", identificador=slug)
        return CuentaInteractiva.tomar(slug=slug)
    return None


def _cargar_modelo_simple(modelo: str, de_serie: SerializedDb, excluir_campos: list[str] = None) -> None:
    """ Carga modelos que no incluyan foreignfields, polimorfismo u otras complicaciones"""
    print(f"Cargando elementos del modelo {modelo}", end=" ")
    excluir_campos = excluir_campos or []
    serie_modelo = de_serie.filter_by_model(modelo)
    Modelo: type | MiModel = apps.get_model(*modelo.split("."))

    for elemento in serie_modelo:
        fields = {k: v for k, v in elemento.fields.items() if k not in excluir_campos}
        Modelo.crear(**fields)
    print("- OK")


def _cargar_cotizaciones(de_serie: SerializedDb):
    cotizaciones = de_serie.filter_by_model("diario.cotizacion")
    print("Cargando elementos del modelo cotizaciones", end=" ")
    for elemento in cotizaciones:
        fields = {k: v for k, v in elemento.fields.items()}
        fields["moneda"] = Moneda.tomar(monname=fields["moneda"][0])
        Cotizacion.crear(**fields)
    print("- OK")


def _tomar_cuenta_ser(
        slug: str | None,
        container: SerializedDb | None) -> CuentaSerializada | None:
    """ Toma y devuelve una cuenta serializada de un contenedor a partir del slug """
    if slug is None or container is None:
        return None
    return CuentaSerializada(container.tomar(model="diario.cuenta", slug=slug))


def _mov_es_traspaso_a_subcuenta(
        movimiento: MovimientoSerializado,
        cuenta: CuentaSerializada,
        cuentas: SerializedDb[CuentaSerializada],
) -> bool:
    if movimiento.es_entrada_o_salida():
        return False

    pos_cuenta = "cta_entrada" if movimiento.fields["cta_entrada"] == [cuenta.fields["slug"]] else "cta_salida"
    pos_contracuenta = "cta_salida" if pos_cuenta == "cta_entrada" else "cta_entrada"
    slug_contracuenta = _slug_cuenta_mov(movimiento, pos_contracuenta, cuentas)
    if CuentaInteractiva.filtro(slug=slug_contracuenta).exists():
        return False

    contracuenta_ser = _tomar_cuenta_ser(slug_contracuenta, container=cuentas)
    if not contracuenta_ser.es_subcuenta_de(cuenta):
        return False

    return True


def _contracuenta_db(
        movimiento: MovimientoSerializado,
        pos_contracuenta: str,
        cuentas: SerializedDb[CuentaSerializada]
) -> CuentaInteractiva | None:
    return _tomar_o_crear_cuenta(
        _tomar_cuenta_ser(
            slug=_slug_cuenta_mov(movimiento, pos_contracuenta, cuentas),
            container=cuentas
        )
    )


def _subcuentas_originales(
        subcuentas_cuenta: SerializedDb[CuentaSerializada],
        fecha_conversion: datetime.date,
        traspasos_de_saldo: SerializedDb[MovimientoSerializado],
        slugs_subcuentas_con_saldo: list[str],
) -> list[dict[str, str | float | Titular]]:
    result = []
    for subc in subcuentas_cuenta.filtrar(fecha_creacion=fecha_conversion):
        slug_subc = subc.fields["slug"]
        # Si la subcuenta tiene saldo
        try:
            mov = traspasos_de_saldo[slugs_subcuentas_con_saldo.index(slug_subc)]
            esgratis = mov.fields["id_contramov"] is None
            saldo = traspasos_de_saldo.tomar(
                **{mov.pos_cta_receptora: [slug_subc]}
            ).fields["_importe"]
            # TODO: ¿Esto que sigue no debería ser responsabilidad de dividir_entre?:
            if mov.pos_cta_receptora == "cta_salida":
                saldo = -saldo
        except ValueError:  # slug_subc no está en slugs_subcuentas_con_saldo
            saldo = 0
            esgratis = False

        result.append({
            "nombre": subc.fields["nombre"],
            "slug": subc.fields["slug"],
            "titular": Titular.tomar(titname=subc.titname()),
            "saldo": saldo,
            "esgratis": esgratis,
        })

    return result


def _subcuentas_agregadas(
        subcuentas_cuenta: SerializedDb[CuentaSerializada],
        fecha_conversion: datetime.date
) -> list[list[str | datetime.date | Titular]]:
    return [[
        x.fields["nombre"],
        x.fields["slug"],
        Titular.tomar(titname=x.titname()),
        x.fields["fecha_creacion"]
    ]
        for x in subcuentas_cuenta
        if x.fields["fecha_creacion"] > fecha_conversion
    ]


def _cargar_cuenta_acumulativa_y_movimientos_anteriores_a_su_conversion(
        cuentas: SerializedDb[CuentaSerializada],
        cuenta: CuentaSerializada,
        cuenta_db: Cuenta,
        movimientos_cuenta: SerializedDb[MovimientoSerializado]):
    print(f"Cargando cuenta acumulativa <{cuenta_db.nombre}>", end=" ")

    traspasos_de_saldo = SerializedDb()

    for movimiento in movimientos_cuenta:
        pos_cuenta = "cta_entrada" if movimiento.fields["cta_entrada"] == [cuenta.fields["slug"]] \
            else "cta_salida"
        pos_contracuenta = "cta_salida" if pos_cuenta == "cta_entrada" else "cta_entrada"

        # Suponemos que cualquier movimiento de la cuenta que no sea de traspaso es anterior a su
        # conversión en acumulativa, así que lo creamos.
        if _mov_es_traspaso_a_subcuenta(movimiento, cuenta, cuentas):
            movimiento.pos_cta_receptora = pos_contracuenta
            traspasos_de_saldo.append(movimiento)
        else:
            cuentas_del_mov = {
                pos_cuenta: cuenta_db,
                pos_contracuenta: _contracuenta_db(movimiento, pos_contracuenta, cuentas)
            }
            print(
                f"Creando movimiento {movimiento.fields['orden_dia']} "
                f"del {movimiento.fields['dia'][0]}: {movimiento.fields['concepto']}",
                end=" "
            )
            Movimiento.crear(
                fecha=movimiento.fields['dia'][0],
                orden_dia=movimiento.fields['orden_dia'],
                concepto=movimiento.fields['concepto'],
                importe=movimiento.fields['_importe'],
                moneda=Moneda.tomar(
                    monname=movimiento.fields['moneda'][0]
                ),
                cotizacion=movimiento.fields['_cotizacion'],
                id_contramov=movimiento.fields['id_contramov'],
                es_automatico=movimiento.fields['es_automatico'],
                esgratis=movimiento.fields['id_contramov'] is None,
                **cuentas_del_mov
            )
            print("- OK")

    # Una vez terminados de recorrer los movimientos de la cuenta y ya
    # generados los movimientos anteriores a su conversión, se procede
    # a la división de la cuenta en subcuentas y su consiguiente conversión
    # en acumulativa.
    # Si hay movimientos marcados como traspasos de saldo, los usamos para
    # tomar el dato del saldo traspasado desde la cuenta acumulativa
    # a sus subcuentas al momento de la conversión.
    slugs_subcuentas_con_saldo = [mov.fields[mov.pos_cta_receptora][0] for mov in traspasos_de_saldo]

    # Buscar las subcuentas en las que está dividida la cuenta
    subcuentas_cuenta = cuentas.filtrar(cta_madre=[cuenta.fields["slug"]])

    # De las subcuentas encontradas, usar aquellas cuya fecha de creación
    # coincide con la fecha de conversión de la cuenta en acumulativa
    # para dividir y convertir la cuenta.
    fecha_conversion = cuenta.campos_polimorficos()["fecha_conversion"]

    subcuentas_conversion = _subcuentas_originales(
        subcuentas_cuenta, fecha_conversion, traspasos_de_saldo, slugs_subcuentas_con_saldo
    )
    cuenta_db = cuenta_db.dividir_y_actualizar(
        *subcuentas_conversion,
        fecha=datetime.date(*[int(x) for x in fecha_conversion.split("-")])
    )

    # Se agregan las subcuentas cuya fecha de creación es posterior
    # a la fecha de conversión de la cuenta en acumulativa
    # (creadas mediante el método CuentaAcumulativa.agregar_subcuenta)
    subcuentas_agregadas = _subcuentas_agregadas(subcuentas_cuenta, fecha_conversion)
    for subcuenta in subcuentas_agregadas:
        cuenta_db.agregar_subcuenta(*subcuenta)

    print("- OK")


def _cargar_cuentas_y_movimientos(
        cuentas: SerializedDb[CuentaSerializada],
        movimientos: SerializedDb[MovimientoSerializado]) -> None:

    print("Cargando cuentas y movimientos")

    cuentas_independientes = SerializedDb([x for x in cuentas if x.es_cuenta_independiente()])
    for cuenta in cuentas_independientes:
        cuenta_db = _tomar_o_crear_cuenta(cuenta)

        if cuenta.es_acumulativa():
            # Buscar posibles movimientos en los que haya intervenido la cuenta
            # antes de convertirse en acumulativa
            movimientos_cuenta = SerializedDb([x for x in movimientos if x.involucra_cuenta(cuenta)])

            _cargar_cuenta_acumulativa_y_movimientos_anteriores_a_su_conversion(
                cuentas, cuenta, cuenta_db, movimientos_cuenta)

            # Retirar de serie movimientos los movimientos de la cuenta acumulativa procesada
            movimientos = SerializedDb([x for x in movimientos if x not in movimientos_cuenta])

    # Una vez cargadas las cuentas y los movimientos relacionados con cuentas acumulativas,
    # cargamos los movimientos normales relacionados con cuentas normales (excluyendo los
    # no generados manualmente).

    for movimiento in movimientos.filtrar(es_automatico=False):
        print(
            f"Creando movimiento {movimiento.fields['orden_dia']} "
            f"del {movimiento.fields['dia'][0]}: {movimiento.fields['concepto']}",
            end=" "
        )
        Movimiento.crear(
            fecha=movimiento.fields['dia'][0],
            orden_dia=movimiento.fields['orden_dia'],
            concepto=movimiento.fields['concepto'],
            importe=movimiento.fields['_importe'],
            cta_entrada=_cuenta_mov(movimiento, "cta_entrada", cuentas),
            cta_salida=_cuenta_mov(movimiento, "cta_salida", cuentas),
            moneda=Moneda.tomar(
                monname=movimiento.fields['moneda'][0]
            ),
            cotizacion=movimiento.fields['_cotizacion'],
            id_contramov=movimiento.fields['id_contramov'],
            es_automatico=movimiento.fields['es_automatico'],
            esgratis=movimiento.fields['id_contramov'] is None,
        )
        print("- OK")
    print("Se cargaron cuentas y movimientos")


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
        _cargar_cotizaciones(db_full)

        cuentas = CuentaSerializada.todes(container=db_full)
        movimientos = MovimientoSerializado.todes(container=db_full)
        _cargar_cuentas_y_movimientos(cuentas, movimientos)
