import pytest

from diario.models import Moneda


@pytest.fixture
def moneda() -> Moneda:
    return Moneda.crear(
        nombre='Moneda',
        monname='mn',
        cotizacion=1.0,
    )


@pytest.fixture
def moneda_2() -> Moneda:
    return Moneda.crear(
        nombre='Currency',
        monname='cr',
        cotizacion=805.0,
    )
