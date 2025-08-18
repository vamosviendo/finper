from datetime import date
from unittest.mock import MagicMock

import pytest

from diario.models import Titular


@pytest.fixture
def titular(fecha_inicial: date) -> Titular:
    return Titular.crear(sk='titular', nombre='Titular', fecha_alta=fecha_inicial)


@pytest.fixture
def otro_titular(fecha_inicial: date) -> Titular:
    return Titular.crear(sk='otro', nombre='Otro Titular', fecha_alta=fecha_inicial)


@pytest.fixture
def titular_gordo(fecha_temprana: date) -> Titular:
    return Titular.crear(sk='gordo', nombre='Titular Gordo', fecha_alta=fecha_temprana)


@pytest.fixture
def titular_principal(mocker, titular: Titular) -> MagicMock:
    return mocker.patch('diario.models.cuenta.TITULAR_PRINCIPAL', titular.sk)
