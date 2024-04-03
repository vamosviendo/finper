from datetime import date
from unittest.mock import MagicMock

import pytest

from diario.models import Titular


@pytest.fixture
def titular(fecha_temprana: date) -> Titular:
    return Titular.crear(titname='titular', nombre='Titular', fecha_alta=fecha_temprana)


@pytest.fixture
def otro_titular(fecha: date) -> Titular:
    return Titular.crear(titname='otro', nombre='Otro Titular', fecha_alta=fecha)


@pytest.fixture
def titular_gordo(fecha: date) -> Titular:
    return Titular.crear(titname='gordo', nombre='Titular Gordo', fecha_alta=fecha)


@pytest.fixture
def titular_principal(mocker, titular: Titular) -> MagicMock:
    return mocker.patch('diario.models.cuenta.TITULAR_PRINCIPAL', titular.titname)
