from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from diario.models import Dia, Movimiento, Titular, CuentaInteractiva


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
        titular: Titular,
        cuenta: CuentaInteractiva,
        dia_temprano: Dia,
        dia_tardio_con_movs: Dia,
        dia_posterior_con_movs: Dia,
        dia_anterior_con_movs: Dia,
        dia_tardio_plus: Dia,
        dia_hoy: Dia) -> QuerySet[Dia]:
    titular.fecha_alta = date(2001, 1, 2)
    titular.clean_save()
    cuenta.fecha_creacion = date(2001, 1, 2)
    cuenta.clean_save()
    Movimiento.crear(fecha=dia_temprano.fecha, concepto="mov", cta_entrada=cuenta, importe=100)
    Movimiento.crear(fecha=dia_tardio_plus.fecha, concepto="mov", cta_entrada=cuenta, importe=100)
    Movimiento.crear(fecha=dia_hoy.fecha, concepto="mov", cta_entrada=cuenta, importe=100)
    Movimiento.crear(
        fecha=date(2001, 1, 2), concepto="mov", cta_entrada=cuenta, importe=100)
    return Dia.todes()


@pytest.fixture
def mas_de_15_dias_con_dias_sin_movimientos(
        mas_de_7_dias: QuerySet[Dia],
        fecha_tardia: date,
        fecha: date,
        cuenta: CuentaInteractiva) -> QuerySet[Dia]:
    Dia.crear(fecha=fecha_tardia - timedelta(1))
    for x in range(1, 9):
        fecha_dia = fecha + timedelta(x)
        Movimiento.crear(fecha=fecha_dia, concepto=f"mov día {fecha_dia}", cta_entrada=cuenta, importe=100)
    return Dia.todes()
