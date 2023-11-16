from typing import Optional
from unittest.mock import MagicMock

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
        plural='dólares',
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


@pytest.fixture(autouse=True)
def mock_moneda_base(mocker, request) -> Optional[MagicMock]:
    if 'nomonbase' in request.keywords:
        return
    peso = request.getfixturevalue('peso')
    return mocker.patch('diario.utils.utils_moneda.MONEDA_BASE', peso.monname)
