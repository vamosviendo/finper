from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from diario.models import Dia, Movimiento, Cuenta, Titular


@pytest.fixture
def dia_temprano(fecha_temprana: date) -> Dia:
    return Dia.crear(fecha=fecha_temprana)


@pytest.fixture
def dia_anterior(fecha_anterior: date) -> Dia:
    return Dia.crear(fecha=fecha_anterior)


@pytest.fixture
def dia_anterior_con_movs(dia_anterior: Dia, entrada_anterior: Movimiento) -> Dia:
    return dia_anterior


@pytest.fixture
def dia(fecha: date) -> Dia:
    try:
        return Dia.crear(fecha=fecha)
    except ValidationError:
        return Dia.tomar(fecha=fecha)


@pytest.fixture
def dia_con_movs(dia: Dia, entrada: Movimiento, salida: Movimiento, traspaso: Movimiento) -> Dia:
    return dia


@pytest.fixture
def dia_posterior(fecha_posterior: date) -> Dia:
    return Dia.crear(fecha=fecha_posterior)


@pytest.fixture
def dia_posterior_con_movs(dia_posterior: Dia, salida_posterior: Movimiento) -> Dia:
    return dia_posterior


@pytest.fixture
def dia_tardio(fecha_tardia: date) -> Dia:
    return Dia.crear(fecha=fecha_tardia)


@pytest.fixture
def dia_tardio_con_movs(dia_tardio: Dia, entrada_tardia: Movimiento) -> Dia:
    return dia_tardio


@pytest.fixture
def dia_tardio_plus(fecha_tardia_plus: date) -> Dia:
    return Dia.crear(fecha=fecha_tardia_plus)


@pytest.fixture
def dia_hoy() -> Dia:
    return Dia.crear(fecha=date.today())


@pytest.fixture
def mas_de_7_dias(
        dia_con_movs: Dia,
        dia_temprano: Dia,
        dia_tardio_con_movs: Dia,
        dia_posterior_con_movs: Dia,
        dia_anterior_con_movs: Dia,
        dia_tardio_plus: Dia,
        dia_hoy: Dia) -> QuerySet[Dia]:
    titular = Titular.crear(nombre="titular_creado", titname="titc", fecha_alta=date(2001, 1, 2))
    cuenta = Cuenta.crear("cuenta_creada", "ccr", titular=titular, fecha_creacion=date(2001, 1, 2))
    Movimiento.crear(fecha=dia_temprano.fecha, concepto="mov", cta_entrada=cuenta, importe=100)
    Movimiento.crear(fecha=dia_tardio_plus.fecha, concepto="mov", cta_entrada=cuenta, importe=100)
    Movimiento.crear(fecha=dia_hoy.fecha, concepto="mov", cta_entrada=cuenta, importe=100)
    Movimiento.crear(
        fecha=date(2001, 1, 2), concepto="mov", cta_entrada=cuenta, importe=100)
    return Dia.todes()
