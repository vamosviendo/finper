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
from utils.errors import ElementoSerializadoInexistente
from vvmodel.models import MiModel
from vvmodel.serializers import SerializedDb, SerializedObject


def info(value: any, msj: str) -> any:
    print(str)
    return value


def _crear_o_tomar(cuenta: CuentaSerializada) -> Cuenta:
    """ Intenta crear una cuenta en la base de datos a partir de una
        cuenta serializada. Si la cuenta ya existe (¿como contracuenta de
        un crédito, por ejemplo?), la toma.
        Devuelve la cuenta creada o tomada de la base de datos"""
    try:
        print(f"Creando cuenta <{cuenta.fields['nombre']}>", end=" ")
        return info(
            Cuenta.crear(
                nombre=cuenta.fields["nombre"],
                slug=cuenta.fields["slug"],
                cta_madre=None,
                fecha_creacion=cuenta.fields["fecha_creacion"],
                titular=Titular.tomar(titname=cuenta.titname()),
                moneda=Moneda.tomar(monname=cuenta.fields["moneda"][0]),
            ),
            msj="- OK"
        )
    except ValidationError:
        print(f"Tomando cuenta existente <{cuenta.fields['nombre']}>", end=" ")
        return info(Cuenta.tomar(slug=cuenta.fields["slug"]), msj="- OK")


def _slug_cuenta_mov(movimiento: MovimientoSerializado, posicion: str) -> str:
    """ Toma un movimiento y devuelve el slug de la cuenta interviniente
        en la posición indicada. """
    if posicion not in ["entrada", "salida"]:
        raise ValueError('Los valores aceptados para posicion son "entrada" y "salida"')
    cta = movimiento.fields[f"cta_{posicion}"]
    slug = cta[0] if cta else None
    # Si la cuenta del movimiento no existe como objeto serializado, lanzar excepción
    if slug and slug not in [x.fields["slug"] for x in cuentas.filter_by_model("diario.cuenta")]:
        raise ElementoSerializadoInexistente(modelo="diario.cuenta", identificador=slug)
    return slug


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


def _cargar_cuentas_y_movimientos(de_serie: SerializedDb) -> None:
    def _tomar_cuenta_ser(
            slug: str | None,
            container: SerializedDb | None) -> CuentaSerializada | None:
        """ Toma y devuelve una cuenta serializada de un contenedor a partir del slug """
        if slug is None or container is None:
            return None
        return CuentaSerializada(container.tomar(model="diario.cuenta", slug=slug))

    print("Cargando cuentas y movimientos")
    global cuentas
    cuentas = CuentaSerializada.todes(container=de_serie)
    movimientos = MovimientoSerializado.todes(container=de_serie)

    cuentas_independientes = SerializedDb([x for x in cuentas if x.es_cuenta_independiente()])
    for cuenta in cuentas_independientes:
        cuenta_db = _crear_o_tomar(cuenta)

        if cuenta.es_acumulativa():
            # Buscar posibles movimientos en los que haya intervenido la cuenta
            # antes de convertirse en acumulativa
            movimientos_cuenta = SerializedDb([
                x for x in movimientos if x.involucra_cuenta(cuenta)
            ])

            # En este intrincado movimiento, que tendré que tratar de simplificar luego, hago lo siguiente:
            # Recorro los movimientos en los que interviene la cuenta, verificando que la cuenta de entrada
            # y la cuenta de salida, en caso de tenerlas, existan. Si es el caso, las guardaremos en
            # sendas variables.
            # En caso de que alguna de las dos cuentas no exista en la base de datos, las posibilidades son:
            #   - Que la cuenta no exista tampoco en la serialización, en cuyo caso debe lanzarse una excepción
            #   - Que la cuenta aparezca en la base de datos posteriormente y por lo tanto todavía no se la haya
            #     (re)creado en la base de datos, pero se la va a crear luego. Este segundo caso a su vez se
            #     divide en dos opciones:
            #     - Que la cuenta madre de esta cuenta sea la cuenta que está siendo procesada, en cuyo caso
            #       señalamos la posición de la cuenta receptora de saldo como cuenta de entrada o de salida
            #       en el movimiento, y guardamos el movimiento en una lista de traspasos de saldo, que usaremos
            #       luego para la división de la cuenta.
            #     - Que sea una cuenta independiente, en cuyo caso deberíamos crearla antes de generar el
            #             movimiento
            traspasos_de_saldo = SerializedDb()

            for movimiento in movimientos_cuenta:
                mov_es_anterior_a_conversion = True
                slug_ce = _slug_cuenta_mov(movimiento, "entrada")
                ce_serializada = _tomar_cuenta_ser(slug_ce, container=cuentas)

                def _todo_el_try_except_que_sigue_de_alguna_manera_y_para_ambas_cuentas(slug):
                    pass

                try:
                    # Si el movimiento serializado tiene cuenta de entrada, buscar la cuenta en la base de datos
                    ce = CuentaInteractiva.tomar(slug=slug_ce) if slug_ce is not None else None
                except CuentaInteractiva.DoesNotExist:
                    # Si no se encuentra la cuenta en la base de datos (damos por sentado que sí existe
                    # en la serialización porque lo chequeamos hace un rato, cosa que tal vez debería hacerse
                    # acá) guardamos el movimiento en una SerializedDb para usarlo luego en la division de
                    # la cuenta.
                    # Antes de eso, deberíamos chequear que la cuenta que estamos procesando sea cuenta madre
                    # de la cuenta faltante. Si es así, hacer esto. De lo contrario generar la subcuenta.
                    if ce_serializada.fields["cta_madre"] != [cuenta.fields["slug"]]:
                        ce = Cuenta.crear(
                            nombre=ce_serializada.fields["nombre"],
                            slug=ce_serializada.fields["slug"],
                            cta_madre=ce_serializada.fields["cta_madre"],
                            fecha_creacion=ce_serializada.fields["fecha_creacion"],
                            titular=Titular.tomar(titname=ce_serializada.titname()),
                            moneda=Moneda.tomar(monname=ce_serializada.fields["moneda"][0]),
                        )
                    else:
                        mov_es_anterior_a_conversion = False
                        movimiento.pos_cta_receptora = "cta_entrada"
                        traspasos_de_saldo.append(movimiento)
                        ce = None

                # Se repite el mismo proceso para cuenta de salida
                slug_cs = _slug_cuenta_mov(movimiento, "salida")
                cs_serializada = _tomar_cuenta_ser(slug_cs, container=cuentas)
                try:
                    cs = CuentaInteractiva.tomar(
                        slug=movimiento.fields['cta_salida'][0]
                    ) if movimiento.fields['cta_salida'] is not None else None
                except CuentaInteractiva.DoesNotExist:
                    if cs_serializada.fields["cta_madre"] != [cuenta.fields["slug"]]:
                        cs = Cuenta.crear(
                            nombre=cs_serializada.fields["nombre"],
                            slug= cs_serializada.fields["slug"],
                            cta_madre=cs_serializada.fields["cta_madre"],
                            fecha_creacion=cs_serializada.fields["fecha_creacion"],
                            titular=Titular.tomar(titname=cs_serializada.titname()),
                            moneda=Moneda.tomar(monname=cs_serializada.fields["moneda"][0]),
                        )
                    else:
                        mov_es_anterior_a_conversion = False
                        movimiento.pos_cta_receptora = "cta_salida"
                        traspasos_de_saldo.append(movimiento)
                        cs = None

                # En caso de que *no* haya una cuenta aún no existente en la base de datos entre las cuentas
                # intervinientes en el movimiento, se supone que el movimiento se produjo antes que la cuenta
                # se convirtiera en acumulativa y se lo genera a partir de los datos del objeto serializado
                # correspondiente.
                if mov_es_anterior_a_conversion:
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

            # Se arma la lista de subcuentas que se usará para la conversión
            # de la cuenta en acumulativa.
            subcuentas_fecha_conversion = []
            for subc in subcuentas_cuenta.filtrar(fecha_creacion=fecha_conversion):
                slug_subc = subc.fields["slug"]
                # Si la subcuenta tiene saldo
                if slug_subc in slugs_subcuentas_con_saldo:
                    mov = traspasos_de_saldo[slugs_subcuentas_con_saldo.index(slug_subc)]
                    saldo = traspasos_de_saldo.tomar(**{mov.pos_cta_receptora: [slug_subc]}).fields["_importe"]
                    # TODO: ¿Esto no debería ser responsabilidad de dividir_entre?:
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
                
            cuenta_db = cuenta_db.dividir_y_actualizar(
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
                cuenta_db.agregar_subcuenta(*subcuenta)

            # Retirar de serie movimientos los movimientos de la cuenta acumulativa procesada
            movimientos = SerializedDb([x for x in movimientos if x not in movimientos_cuenta])

    # Una vez cargadas las cuentas y los movimientos relacionados con cuentas acumulativas,
    # cargamos los movimientos normales relacionados con cuentas normales (excluyendo los
    # no generados manualmente).
    for movimiento in movimientos.filtrar(es_automatico=False):
        slug_ce = movimiento.fields["cta_entrada"][0] if movimiento.fields["cta_entrada"] else None
        if slug_ce and slug_ce not in [x.fields["slug"] for x in cuentas.filter_by_model("diario.cuenta")]:
            raise ElementoSerializadoInexistente(modelo="diario.cuenta", identificador=slug_ce)
        ce = CuentaInteractiva.tomar(slug=slug_ce) if slug_ce else None

        slug_cs = movimiento.fields["cta_salida"][0] if movimiento.fields["cta_salida"] else None
        if slug_cs and slug_cs not in [x.fields["slug"] for x in cuentas.filter_by_model("diario.cuenta")]:
            raise ElementoSerializadoInexistente(modelo="diario.cuenta", identificador=slug_cs)
        cs = CuentaInteractiva.tomar(slug=slug_cs) if slug_cs else None

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
        _cargar_cuentas_y_movimientos(db_full)
