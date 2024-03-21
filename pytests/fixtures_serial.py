from pathlib import Path

import pytest

from django.core.management import call_command

from vvmodel.serializers import load_serialized_filename, SerializedDb


@pytest.fixture
def db_serializada() -> SerializedDb:
    call_command('serializar_db')
    yield load_serialized_filename("db_full.json")
    Path('db_full.json').unlink()
