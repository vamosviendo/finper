from pathlib import Path

import pytest

from django.apps import apps
from django.core.management import call_command

from diario.models import Cotizacion
from diario.serializers import MovimientoSerializado, DiaSerializado, SaldoSerializado
from utils.archivos import es_json_valido


@pytest.fixture(autouse=True)
def borrar_db_full():
    yield
    Path('db_full.json').unlink(missing_ok=True)


@pytest.fixture
def varios_titulares(titular, otro_titular, titular_gordo):
    return [titular, otro_titular, titular_gordo]


@pytest.fixture
def varias_monedas(peso, dolar, euro):
    return [peso, dolar, euro]


@pytest.fixture
def varias_cuentas(
        cuenta, cuenta_2, cuenta_3, cuenta_ajena, cuenta_acumulativa,
        cuenta_acumulativa_en_dolares, cuenta_en_dolares):
    return [
        cuenta, cuenta_2, cuenta_3, cuenta_ajena, cuenta_acumulativa,
        cuenta_acumulativa_en_dolares, cuenta_en_dolares
    ]


@pytest.fixture
def varios_movimientos(
        entrada, salida, entrada_tardia, traspaso, traspaso_posterior, credito,
        entrada_temprana, entrada_cuenta_ajena, entrada_en_dolares,
        salida_tardia_tercera_cuenta):
    return [
        entrada, salida, entrada_tardia, traspaso, traspaso_posterior, credito,
        entrada_temprana, entrada_cuenta_ajena, entrada_en_dolares,
        salida_tardia_tercera_cuenta
    ]


@pytest.fixture
def varios_dias(dia_temprano, dia_anterior, dia, dia_posterior, dia_tardio, dia_tardio_plus):
    return [dia_temprano, dia_anterior, dia, dia_posterior, dia_tardio, dia_tardio_plus]


def test_genera_archivo_db_full_json():
    call_command('serializar_db')
    db_full = Path('db_full.json')
    assert db_full.exists()


def test_archivo_generado_es_json_valido():
    call_command('serializar_db')
    with open('db_full.json', 'r') as db_full:
        assert es_json_valido(db_full)


@pytest.mark.parametrize("modelo, elementos, identificador, key", [
    ("titular", "varios_titulares", "sk", None),
    ("moneda", "varias_monedas", "sk", None),
    ("cuenta", "varias_cuentas", "sk", None),
])
def test_serializa_todos_los_titulares_monedas_y_cuentas_de_la_base_de_datos_en_json(
        modelo, elementos, identificador, key, request):
    key = key or identificador
    elementos = request.getfixturevalue(elementos)
    db_serializada = request.getfixturevalue("db_serializada")
    elementos_ser = db_serializada.filter_by_model(f"diario.{modelo}")
    assert len(elementos_ser) == apps.get_model("diario", modelo).cantidad()
    for elem in elementos:
        assert getattr(elem, identificador) in [
            es.fields[key] for es in elementos_ser
        ]


def test_serializa_todas_las_cotizaciones_de_la_base_de_datos_en_json(
        varias_monedas, cotizacion_posterior, cotizacion_tardia, db_serializada):
    cotizaciones = db_serializada.filter_by_model("diario.cotizacion")
    assert len(cotizaciones) == Cotizacion.cantidad()
    for cotizacion in Cotizacion.todes():
        assert \
            ([cotizacion.moneda.sk], str(cotizacion.fecha)) in \
            [(cot.fields['moneda'], cot.fields['fecha']) for cot in cotizaciones]


@pytest.mark.parametrize("modelo", ["cuentainteractiva", "cuentaacumulativa"])
def test_serializa_todas_las_cuentas_interactivas_y_acumulativas(modelo, varias_cuentas, db_serializada):
    cuentas_ser = db_serializada.filter_by_model("diario.cuenta")
    cuentas_subc_ser = db_serializada.filter_by_model(f"diario.{modelo}")
    for cuenta_int in cuentas_subc_ser:
        cuenta_int.fields.update(next(x.fields for x in cuentas_ser if x.pk == cuenta_int.pk))
    clase_modelo = apps.get_model("diario", modelo)
    assert len(cuentas_subc_ser) == clase_modelo.cantidad()
    for ci in clase_modelo.todes():
        assert ci.sk in [cis.fields['sk'] for cis in cuentas_subc_ser]


@pytest.mark.parametrize(
    "elementos, modelo, tipo", [
        ("varios_movimientos", "movimiento", MovimientoSerializado),
        ("varios_dias", "dia", DiaSerializado),
        ("varios_movimientos", "saldo", SaldoSerializado),
    ])
def test_serializa_todos_los_movimientos_dias_y_saldos_de_la_base_de_datos(
        elementos, modelo, tipo, request):
    request.getfixturevalue(elementos)
    db_serializada = request.getfixturevalue("db_serializada")
    elementos_ser = [tipo(x) for x in db_serializada.filter_by_model(f"diario.{modelo}")]
    Modelo = apps.get_model("diario", modelo)
    assert len(elementos_ser) == Modelo.cantidad()

    identidades = [x.identidad for x in elementos_ser]
    for elemento in Modelo.todes():
        assert elemento.identidad in identidades


def test_serializa_cuentas_y_movimientos_con_natural_key_moneda(entrada, db_serializada):
    cta = db_serializada.primere("diario.cuenta")
    mov = db_serializada.primere("diario.movimiento")
    assert cta.fields['moneda'] == [entrada.cta_entrada.moneda.sk]
    assert mov.fields['moneda'] == [entrada.moneda.sk]


def test_serializa_cuentas_interactivas_con_natural_key_titular(cuenta, db_serializada):
    cta = db_serializada.primere("diario.cuentainteractiva")
    assert cta.fields['titular'] == [cuenta.titular.sk]


def test_serializa_cuentas_acumulativas_con_natural_key_titular_original(cuenta_acumulativa, db_serializada):
    cta = db_serializada.primere("diario.cuentaacumulativa")
    assert cta.fields['titular_original'] == [cuenta_acumulativa.titular_original.sk]


def test_serializa_cuentas_con_natural_key_cta_madre(cuenta_acumulativa, db_serializada):
    cta = db_serializada.primere("diario.cuenta", sk="scs1")
    assert cta.fields["cta_madre"] == [cuenta_acumulativa.sk]


def test_serializa_movimientos_con_natural_keys_cta_entrada_cta_salida(traspaso, db_serializada):
    mov = db_serializada.primere("diario.movimiento", concepto="Traspaso")
    assert mov.fields["cta_entrada"] == [traspaso.cta_entrada.sk]
    assert mov.fields["cta_salida"] == [traspaso.cta_salida.sk]


def test_serializa_movimientos_con_natural_key_dia(entrada, db_serializada):
    mov = db_serializada.primere("diario.movimiento", concepto="Entrada")
    assert mov.fields["dia"] == [str(entrada.dia)]

def test_serializa_saldos_con_natural_key_cuenta(saldo, db_serializada):
    sdo = db_serializada.primere(
        "diario.saldo",
        movimiento=[str(saldo.movimiento.dia), saldo.movimiento.orden_dia]
    )
    assert sdo.fields["cuenta"] == [saldo.cuenta.sk]

def test_serializa_saldos_con_natural_key_movimiento(saldo, db_serializada):
    sdo = db_serializada.primere("diario.saldo", cuenta=[saldo.cuenta.sk])
    assert \
        sdo.fields["movimiento"] == [str(saldo.movimiento.dia), saldo.movimiento.orden_dia]
