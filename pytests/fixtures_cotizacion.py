from datetime import date

import pytest

from diario.models import Moneda, Cotizacion


@pytest.fixture
def cotizacion(dolar: Moneda, fecha: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha, importe=335)


@pytest.fixture
def cotizacion_posterior(dolar: Moneda, fecha_posterior: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha_posterior, importe=414)


@pytest.fixture
def cotizacion_tardia(dolar: Moneda, fecha_tardia: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha_tardia, importe=837)
