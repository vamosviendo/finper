import pytest

from diario.models import Moneda


@pytest.fixture
def peso() -> Moneda:
    return Moneda.crear(
        nombre='Peso',
        monname='p',
        cotizacion=1.0,
    )


@pytest.fixture
def dolar() -> Moneda:
    return Moneda.crear(
        nombre='Dolar',
        monname='uss',
        cotizacion=805.0,
    )


@pytest.fixture
def euro() -> Moneda:
    return Moneda.crear(
        nombre='Euro',
        monname='eu',
        cotizacion=1105.82,
    )
