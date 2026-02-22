from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from diario.models import Dia, Movimiento, Titular, CuentaInteractiva
from utils.varios import el_que_no_es


@pytest.fixture
def dia_temprano(fecha_temprana: date) -> Dia:
    try:
        return Dia.crear(fecha=fecha_temprana)
    except ValidationError:
        return Dia.tomar(fecha=fecha_temprana)


@pytest.fixture
def dia_anterior(fecha_anterior: date) -> Dia:
    try:
        return Dia.crear(fecha=fecha_anterior)
    except ValidationError:     # Por algún motivo ya existe
        return Dia.tomar(fecha=fecha_anterior)


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
        fecha_inicial: date,
        entrada_temprana,
        entrada_anterior_otra_cuenta,
        entrada, salida, traspaso,
        entrada_posterior_cuenta_ajena,
        entrada_tardia,
        fecha_tardia_plus,
        cuenta, cuenta_2,
):
    Movimiento.crear(fecha=fecha_inicial, concepto="mov inicial", cta_entrada=cuenta, importe=140)
    Movimiento.crear(fecha=fecha_inicial + timedelta(5), concepto="mov siguiente", cta_entrada=cuenta, importe=145)
    Movimiento.crear(fecha=fecha_tardia_plus, concepto="mov tardio plus", cta_salida=cuenta, importe=120)
    Movimiento.crear(
        fecha=fecha_tardia_plus+timedelta(10), concepto="mov_lejano_otra_cuenta", cta_entrada=cuenta_2, importe=130
    )
    Movimiento.crear(
        fecha=fecha_tardia_plus + timedelta(10), concepto="mov_lejano", cta_entrada=cuenta, importe=150
    )
    Movimiento.crear(
        fecha=fecha_tardia_plus + timedelta(20), concepto="mov_ignoto_otra_cuenta", cta_salida=cuenta_2, importe=160
    )
    Movimiento.crear(fecha=fecha_tardia_plus + timedelta(30), concepto="mov_final", cta_entrada=cuenta, importe=170)
    Movimiento.crear(fecha=fecha_tardia_plus + timedelta(35), concepto="mov_final", cta_entrada=cuenta, importe=175)
    return Dia.todes()


@pytest.fixture
def mas_de_7_ds(
        dia_con_movs: Dia,
        titular: Titular,
        cuenta: CuentaInteractiva,
        cuenta_2: CuentaInteractiva,
        dia_temprano: Dia,
        dia_tardio_con_movs: Dia,
        dia_posterior_con_movs: Dia,
        dia_anterior_con_movs: Dia,
        dia_tardio_plus: Dia,
        dia_hoy: Dia,
        fecha_inicial: date) -> QuerySet[Dia]:
    Movimiento.crear(fecha=dia_temprano.fecha, concepto="mov", cta_entrada=cuenta_2, importe=110)
    Movimiento.crear(fecha=dia_tardio_plus.fecha, concepto="mov", cta_entrada=cuenta, importe=120)
    Movimiento.crear(fecha=dia_hoy.fecha, concepto="mov", cta_entrada=cuenta_2, importe=130)
    Movimiento.crear(
        fecha=date(2001, 1, 2), concepto="mov", cta_entrada=cuenta, importe=140)
    return Dia.todes()


@pytest.fixture
def muchos_dias(
        mas_de_7_ds: QuerySet[Dia],
        fecha_tardia: date,
        fecha: date,
        cuenta: CuentaInteractiva,
        cuenta_2: CuentaInteractiva) -> QuerySet[Dia]:
    Dia.crear(fecha=fecha_tardia - timedelta(1))
    c = cuenta
    for x in range(1, 23):
        c = el_que_no_es(c, cuenta, cuenta_2)
        fecha_dia = fecha + timedelta(x)
        Movimiento.crear(fecha=fecha_dia, concepto=f"mov día {fecha_dia}", cta_entrada=c, importe=100)
    assert Dia.cantidad() > 28
    return Dia.todes()


@pytest.fixture
def muchos_dias_distintos_titulares(cuenta, cuenta_2, cuenta_ajena, otro_titular, muchos_dias):
    c = cuenta_2
    for mov in cuenta_2.movs():
        c = el_que_no_es(c, cuenta_2, cuenta_ajena)
        if c == cuenta_ajena:
            mov.cta_entrada = c
            mov.clean_save()
    fecha = Dia.ultime().fecha
    for x in range(1, 14):
        c = el_que_no_es(c, cuenta_2, cuenta_ajena)
        fecha_dia = fecha + timedelta(x)
        Movimiento.crear(fecha=fecha_dia, concepto=f"mov día {fecha_dia}", cta_entrada=c, importe=100)
    return Dia.todes()
