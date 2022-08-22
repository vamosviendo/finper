from datetime import date

import pytest

from diario.models import CuentaInteractiva, Movimiento


@pytest.fixture
def entrada_anterior(cuenta: CuentaInteractiva, fecha_anterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada anterior', importe=3,
        cta_entrada=cuenta, fecha=fecha_anterior
    )


@pytest.fixture
def entrada(cuenta: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada', importe=100, cta_entrada=cuenta, fecha=fecha
    )


@pytest.fixture
def salida(cuenta: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Salida', importe=100, cta_salida=cuenta, fecha=fecha
    )


@pytest.fixture
def traspaso(cuenta: CuentaInteractiva, cuenta_2: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Traspaso', importe=2,
        cta_entrada=cuenta, cta_salida=cuenta_2,
        fecha=fecha
    )


@pytest.fixture
def entrada_posterior_otra_cuenta(cuenta_2: CuentaInteractiva, fecha_posterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada posterior otra cuenta', importe=50,
        cta_entrada=cuenta_2, fecha=fecha_posterior
    )


@pytest.fixture
def salida_posterior(cuenta: CuentaInteractiva, fecha_posterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Salida posterior',
        importe=40,
        cta_salida=cuenta,
        fecha=fecha_posterior
    )


@pytest.fixture
def traspaso_posterior(cuenta: CuentaInteractiva, cuenta_2: CuentaInteractiva, fecha_posterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Traspaso posterior', importe=70,
        cta_entrada=cuenta_2, cta_salida=cuenta,
        fecha=fecha_posterior,
    )


@pytest.fixture
def entrada_tardia(cuenta: CuentaInteractiva, fecha_tardia: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada tardía', importe=80, cta_entrada=cuenta, fecha=fecha_tardia
    )


@pytest.fixture
def credito(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Crédito',
        importe=100,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        fecha=fecha,
    )


@pytest.fixture
def donacion(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Donación',
        importe=100,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        fecha=fecha,
        esgratis=True,
    )


@pytest.fixture
def contramov_credito(credito: Movimiento) -> Movimiento:
    return Movimiento.tomar(id=credito.id_contramov)
