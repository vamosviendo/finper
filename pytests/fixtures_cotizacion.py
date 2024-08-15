from datetime import date

import pytest

from diario.models import Moneda, Cotizacion


@pytest.fixture
def cotizacion(dolar: Moneda, fecha_anterior: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha_anterior, importe=335)


@pytest.fixture
def cotizacion_posterior(dolar: Moneda, fecha_posterior: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha_posterior, importe=414)


@pytest.fixture
def cotizacion_tardia(dolar: Moneda, fecha_tardia: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha_tardia, importe=837)


@pytest.fixture
def cotizacion_euro(euro: Moneda, fecha: date) -> Cotizacion:
    return Cotizacion.tomar(moneda=euro, fecha=fecha)


@pytest.fixture
def cotizacion_posterior_euro(euro: Moneda, fecha_posterior: date) -> Cotizacion:
    return Cotizacion.crear(moneda=euro, fecha=fecha_posterior, importe=455)


@pytest.fixture
def cotizacion_tardia_euro(euro: Moneda, fecha_tardia: date) -> Cotizacion:
    return Cotizacion.crear(moneda=euro, fecha=fecha_tardia, importe=969)
