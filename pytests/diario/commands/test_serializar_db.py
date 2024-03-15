from pathlib import Path

import pytest

from django.apps import apps
from django.core.management import call_command

from utils.archivos import es_json_valido
from vvmodel.serializers import load_serialized_filename


@pytest.fixture(autouse=True)
def borrar_db_full():
    yield
    Path('db_full.json').unlink(missing_ok=True)


@pytest.fixture
def db_serializada():
    call_command('serializar_db')
    yield load_serialized_filename("db_full.json")
    Path('db_full.json').unlink()


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


def test_genera_archivo_db_full_json():
    call_command('serializar_db')
    db_full = Path('db_full.json')
    assert db_full.exists()


def test_archivo_generado_es_json_valido():
    call_command('serializar_db')
    with open('db_full.json', 'r') as db_full:
        assert es_json_valido(db_full)


@pytest.mark.parametrize("modelo, elementos, identificador", [
    ("titular", "varios_titulares", "titname"),
    ("moneda", "varias_monedas", "monname"),
    ("cuenta", "varias_cuentas", "slug"),
    # ("cuentainteractiva", "varias_cuentas", "slug"),
    # ("cuentaacumulativa", "varias_cuentas", "slug"),
])
def test_serializa_todos_los_elementos_de_diario_en_json(modelo, elementos, identificador, request):
    elementos = request.getfixturevalue(elementos)
    db_serializada = request.getfixturevalue("db_serializada")
    elementos_ser = db_serializada.filter_by_model("diario", modelo)
    assert len(elementos_ser) == apps.get_model("diario", modelo).cantidad()
    for elem in elementos:
        assert getattr(elem, identificador) in [
            es.fields[identificador] for es in elementos_ser
        ]


@pytest.mark.parametrize("modelo", ["cuentainteractiva", "cuentaacumulativa"])
def test_serializa_todas_las_cuentas_interactivas(modelo, varias_cuentas, db_serializada):
    cuentas_ser = db_serializada.filter_by_model("diario", "cuenta")
    cuentas_subc_ser = db_serializada.filter_by_model("diario", modelo)
    for cuenta_int in cuentas_subc_ser:
        cuenta_int.fields.update(next(x.fields for x in cuentas_ser if x.pk == cuenta_int.pk))
    clase_modelo = apps.get_model("diario", modelo)
    assert len(cuentas_subc_ser) == clase_modelo.cantidad()
    for ci in clase_modelo.todes():
        assert ci.slug in [cis.fields['slug'] for cis in cuentas_subc_ser]
