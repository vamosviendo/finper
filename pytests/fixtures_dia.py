from datetime import date

import pytest
from django.core.exceptions import ValidationError

from diario.models import Dia


@pytest.fixture
def dia_temprano(fecha_temprana: date) -> Dia:
    return Dia.crear(fecha=fecha_temprana)


@pytest.fixture
def dia_anterior(fecha_anterior: date) -> Dia:
    return Dia.crear(fecha=fecha_anterior)


@pytest.fixture
def dia(fecha: date) -> Dia:
    try:
        return Dia.crear(fecha=fecha)
    except ValidationError:
        return Dia.tomar(fecha=fecha)


@pytest.fixture
def dia_posterior(fecha_posterior: date) -> Dia:
    return Dia.crear(fecha=fecha_posterior)


@pytest.fixture
def dia_tardio(fecha_tardia: date) -> Dia:
    return Dia.crear(fecha=fecha_tardia)


@pytest.fixture
def dia_tardio_plus(fecha_tardia_plus: date) -> Dia:
    return Dia.crear(fecha=fecha_tardia_plus)


@pytest.fixture
def dia_hoy() -> Dia:
    return Dia.crear(fecha=date.today())


@pytest.fixture
def mas_de_7_dias(dia, dia_temprano, dia_tardio, dia_posterior, dia_anterior, dia_tardio_plus, dia_hoy):
    Dia.crear(fecha=date(2001, 1, 2))
    return Dia.todes()
