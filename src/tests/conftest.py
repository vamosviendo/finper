import pytest


pytest_plugins = [
    "tests.fixtures_archivo",
    "tests.fixtures_cotizacion",
    "tests.fixtures_cuenta",
    "tests.fixtures_dia",
    "tests.fixtures_fecha",
    "tests.fixtures_importe",
    "tests.fixtures_moneda",
    "tests.fixtures_movimiento",
    "tests.fixtures_saldo_diario",
    "tests.fixtures_serial",
    "tests.fixtures_titular",
]


@pytest.fixture
def none():
    return None


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.django_db(transaction=True))
