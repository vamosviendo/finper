from pathlib import Path

import pytest

from django.core.management import call_command

from utils.archivos import es_json_valido


@pytest.fixture(autouse=True)
def borrar_db_full():
    yield
    Path('db_full.json').unlink()


def test_genera_archivo_db_full_json():
    call_command('serializar_db')
    db_full = Path('db_full.json')
    assert db_full.exists()


def test_archivo_generado_es_json_valido():
    call_command('serializar_db')
    with open('db_full.json', 'r') as db_full:
        assert es_json_valido(db_full)
