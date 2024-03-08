import json
from pathlib import Path

import pytest

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


def test_genera_archivo_db_full_json():
    call_command('serializar_db')
    db_full = Path('db_full.json')
    assert db_full.exists()


def test_archivo_generado_es_json_valido():
    call_command('serializar_db')
    with open('db_full.json', 'r') as db_full:
        assert es_json_valido(db_full)


def test_serializa_todos_los_titulares(titular, otro_titular, titular_gordo, db_serializada):
    titulares = db_serializada.filter_by_model("diario", "titular")
    assert len(titulares) == 3
    for tit in [titular, otro_titular, titular_gordo]:
        assert tit.titname in [
            t['fields']['titname'] for t in titulares
        ]


def test_serializa_todas_las_monedas_en_json(peso, dolar, euro, db_serializada):
    monedas = db_serializada.filter_by_model("diario", "moneda")
    assert len(monedas) == 3
    for mon in [peso, dolar, euro]:
        assert mon.monname in [
            m['fields']['monname'] for m in monedas
        ]
