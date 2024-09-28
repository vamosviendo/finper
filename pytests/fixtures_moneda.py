from datetime import date
from typing import Optional
from unittest.mock import MagicMock

import pytest

from diario.models import Moneda, Cotizacion


@pytest.fixture
def peso(fecha: date) -> Moneda:
    mon = Moneda.crear(
        nombre='Peso',
        monname='p',
    )
    Cotizacion.crear(moneda=mon, fecha=fecha, importe=1)
    return mon


@pytest.fixture
def dolar(fecha: date) -> Moneda:
    mon = Moneda.crear(
        nombre='Dolar',
        plural='dólares',
        monname='uss',
    )
    Cotizacion.crear(moneda=mon, fecha=fecha, importe=805.0)
    return mon


@pytest.fixture
def euro(fecha: date) -> Moneda:
    mon = Moneda.crear(
        nombre='Euro',
        monname='eu',
    )
    Cotizacion.crear(moneda=mon, fecha=fecha, importe=1100)
    return mon


@pytest.fixture
def real(fecha: date) -> Moneda:
    mon = Moneda.crear(
        nombre='Real',
        plural='Reales',
        monname='r',
    )
    Cotizacion.crear(moneda=mon, fecha=fecha, importe=300)
    return mon


@pytest.fixture
def yen(fecha: date) -> Moneda:
    mon = Moneda.crear(
        nombre='Yen',
        plural='Yenes',
        monname='y',
    )
    Cotizacion.crear(moneda=mon, fecha=fecha, importe=3200)
    return mon


@pytest.fixture(autouse=True)
def mock_moneda_base(mocker, request) -> Optional[MagicMock]:
    if 'nomonbase' in request.keywords:
        return
    peso = request.getfixturevalue('peso')
    return mocker.patch('diario.utils.utils_moneda.MONEDA_BASE', peso.monname)
