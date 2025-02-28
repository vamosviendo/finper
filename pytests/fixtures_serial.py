import json
from pathlib import Path

import pytest

from django.apps import apps
from django.core.management import call_command

from diario.models import Movimiento
from vvmodel.serializers import load_serialized_filename, SerializedDb


@pytest.fixture
def db_serializada() -> SerializedDb:
    call_command('serializar_db')
    yield load_serialized_filename("db_full.json")
    # Descomentar para guardar una copia de la base de datos serializada:
    # import shutil
    # shutil.copyfile("db_full.json", "db_test.json")
    Path('db_full.json').unlink()


@pytest.fixture
def db_serializada_con_datos(
        credito_entre_subcuentas: Movimiento,
        db_serializada: SerializedDb) -> SerializedDb:
    return db_serializada


@pytest.fixture
def vaciar_db():
    for model in apps.all_models['diario']:
        for obj in apps.get_model("diario", model).objects.all():
            obj.delete()
