import pytest


pytest_plugins = [
    "pytests.fixtures_cuenta",
    "pytests.fixtures_dia",
    "pytests.fixtures_fecha",
    "pytests.fixtures_importe",
    "pytests.fixtures_moneda",
    "pytests.fixtures_movimiento",
    "pytests.fixtures_saldo",
    "pytests.fixtures_titular",
]


@pytest.fixture
def none():
    return None
