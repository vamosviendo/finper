import json
from pathlib import Path
from typing import Generator, Any

import pytest

from django.apps import apps
from django.core.management import call_command

from diario.models import Movimiento
from vvmodel.serializers import load_serialized_filename, SerializedDb, SerializedObject


@pytest.fixture
def db_serializada() -> Generator[SerializedDb, Any, None]:
    # Proteger archivo de base de datos serializada si existe
    db_full = Path("db_full.json")
    if db_full.exists():
        db_full.rename("db_full_backup.json")

    call_command('serializar_db')
    yield load_serialized_filename("db_full.json")

    # Descomentar para guardar una copia de la base de datos serializada:
    # import shutil
    # shutil.copyfile("db_full.json", "db_test.json")

    # Reponer archivo de base de datos serializada. Si no existe,
    # eliminar el generado por el fixture.
    db_backup = Path("db_full_backup.json")
    if db_backup.exists():
        db_backup.rename("db_full.json")
    else:
        db_full.unlink()

@pytest.fixture
def db_serializada_legacy(db_serializada: SerializedDb) -> SerializedDb:
   # A los efectos del testeo, cambiar campo sk por antiguo campo titname
    for titular in db_serializada.filter_by_model("diario.titular"):
        titular.fields.update({
            "titname": titular.fields.pop("sk")
        })

    # Reescribir el archivo json
    jsonoutput = [dict(x)for x in db_serializada]
    with open("db_full.json", "w") as db_full:
        json.dump(jsonoutput, db_full, indent=2)

    # return SerializedDb([SerializedObject(x) for x in jsonoutput])
    return db_serializada


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
