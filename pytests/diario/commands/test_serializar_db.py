from pathlib import Path

import pytest

from django.apps import apps
from django.core.management import call_command

from diario.serializers import MovimientoSerializado, DiaSerializado
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
    ("titular", "varios_titulares", "titname", None),
    ("moneda", "varias_monedas", "monname", None),
    ("cuenta", "varias_cuentas", "slug", None),
])
def test_serializa_todos_los_titulares_monedas_cuentas_y_dias_de_la_base_de_datos_en_json(modelo, elementos, identificador, key, request):
    key = key or identificador
    elementos = request.getfixturevalue(elementos)
    db_serializada = request.getfixturevalue("db_serializada")
    elementos_ser = db_serializada.filter_by_model("diario", modelo)
    assert len(elementos_ser) == apps.get_model("diario", modelo).cantidad()
    for elem in elementos:
        assert getattr(elem, identificador) in [
            es.fields[key] for es in elementos_ser
        ]


@pytest.mark.parametrize("modelo", ["cuentainteractiva", "cuentaacumulativa"])
def test_serializa_todas_las_cuentas_interactivas_y_acumulativas(modelo, varias_cuentas, db_serializada):
    cuentas_ser = db_serializada.filter_by_model("diario", "cuenta")
    cuentas_subc_ser = db_serializada.filter_by_model("diario", modelo)
    for cuenta_int in cuentas_subc_ser:
        cuenta_int.fields.update(next(x.fields for x in cuentas_ser if x.pk == cuenta_int.pk))
    clase_modelo = apps.get_model("diario", modelo)
    assert len(cuentas_subc_ser) == clase_modelo.cantidad()
    for ci in clase_modelo.todes():
        assert ci.slug in [cis.fields['slug'] for cis in cuentas_subc_ser]


def test_serializa_todos_los_movimientos(varios_movimientos, db_serializada):
    movimientos_ser = [
        MovimientoSerializado(x) for x in db_serializada.filter_by_model("diario", "movimiento")
    ]
    Movimiento = apps.get_model("diario", "movimiento")
    assert len(movimientos_ser) == Movimiento.cantidad()

    identidades = [m.identidad for m in movimientos_ser]
    for mov in Movimiento.todes():
        assert mov.identidad in identidades


def test_serializa_todos_los_dias(varios_dias, db_serializada):
    dias_ser = [DiaSerializado(x) for x in db_serializada.filter_by_model("diario", "dia")]
    Dia = apps.get_model("diario", "dia")
    assert len(dias_ser) == Dia.cantidad()

    identidades = [d.identidad for d in dias_ser]
    for dia in Dia.todes():
        assert dia.identidad in identidades

@pytest.mark.xfail
def test_serializa_todos_los_saldos(varios_saldos, db_serializada):
    pytest.fail('escribir')
