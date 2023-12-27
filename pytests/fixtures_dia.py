from datetime import date

import pytest

from diario.models import Dia


@pytest.fixture
def dia_temprano(fecha_temprana: date) -> Dia:
    return Dia.crear(fecha=fecha_temprana)


@pytest.fixture
def dia_anterior(fecha_anterior: date) -> Dia:
    return Dia.crear(fecha=fecha_anterior)


@pytest.fixture
def dia(fecha: date) -> Dia:
    return Dia.crear(fecha=fecha)


@pytest.fixture
def dia_posterior(fecha_posterior: date) -> Dia:
    return Dia.crear(fecha=fecha_posterior)


@pytest.fixture
def dia_tardio(fecha_tardia: date) -> Dia:
    return Dia.crear(fecha=fecha_tardia)


@pytest.fixture
def dia_tardio_plus(fecha_tardia_plus: date) -> Dia:
    return Dia.crear(fecha=fecha_tardia_plus)
