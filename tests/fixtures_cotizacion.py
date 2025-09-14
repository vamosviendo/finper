from datetime import date, timedelta
from random import randint

import pytest
from django.db.models import QuerySet

from diario.models import Moneda, Cotizacion


@pytest.fixture
def cotizacion_dolar(dolar: Moneda, fecha_anterior: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha_anterior, importe_compra=335, importe_venta=350)


@pytest.fixture
def cotizacion_posterior_dolar(dolar: Moneda, fecha_posterior: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha_posterior, importe_compra=414, importe_venta=430)


@pytest.fixture
def cotizacion_tardia_dolar(dolar: Moneda, fecha_tardia: date) -> Cotizacion:
    return Cotizacion.crear(moneda=dolar, fecha=fecha_tardia, importe_compra=837, importe_venta=862)


@pytest.fixture
def cotizacion_anterior_euro(euro: Moneda, fecha_anterior: date) -> Cotizacion:
    return Cotizacion.crear(moneda=euro, fecha=fecha_anterior, importe_compra=350, importe_venta=363)


@pytest.fixture
def cotizacion_euro(euro: Moneda, fecha: date) -> Cotizacion:
    return Cotizacion.tomar(moneda=euro, fecha=fecha)


@pytest.fixture
def cotizacion_posterior_euro(euro: Moneda, fecha_posterior: date) -> Cotizacion:
    return Cotizacion.crear(moneda=euro, fecha=fecha_posterior, importe_compra=455, importe_venta=462)


@pytest.fixture
def cotizacion_tardia_euro(euro: Moneda, fecha_tardia: date) -> Cotizacion:
    return Cotizacion.crear(moneda=euro, fecha=fecha_tardia, importe_compra=969, importe_venta=1010)


@pytest.fixture
def mas_de_20_cotizaciones_dolar(dolar: Moneda, fecha: date) -> QuerySet[Cotizacion]:
    for index in range(0,21):
        importe_compra = randint(900, 999)
        Cotizacion.crear(
            moneda=dolar,
            fecha=fecha-timedelta(index),
            importe_compra=importe_compra,
            importe_venta=importe_compra + 10,
        )
    assert dolar.cotizaciones.count() > 20
    return dolar.cotizaciones.all()
