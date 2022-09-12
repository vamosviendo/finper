from datetime import date

import pytest

from diario.models import CuentaInteractiva, Movimiento
from utils.helpers_tests import dividir_en_dos_subcuentas


@pytest.fixture
def entrada_temprana(cuenta: CuentaInteractiva, fecha_temprana: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada temprana', importe=47,
        cta_entrada=cuenta, fecha=fecha_temprana
    )


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
        concepto='Salida', importe=115, cta_salida=cuenta, fecha=fecha
    )


@pytest.fixture
def entrada_cuenta_ajena(cuenta_ajena: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada cuenta ajena', importe=849, cta_entrada=cuenta_ajena, fecha=fecha
    )


@pytest.fixture
def traspaso(cuenta: CuentaInteractiva, cuenta_2: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Traspaso', importe=2,
        cta_entrada=cuenta, cta_salida=cuenta_2,
        fecha=fecha
    )


@pytest.fixture
def entrada_otra_cuenta(cuenta_2: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada', importe=486, cta_entrada=cuenta_2, fecha=fecha
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
def entrada_con_ca(entrada: Movimiento) -> Movimiento:
    dividir_en_dos_subcuentas(entrada.cta_entrada)
    entrada.refresh_from_db()
    return entrada


@pytest.fixture
def salida_con_ca(salida: Movimiento) -> Movimiento:
    dividir_en_dos_subcuentas(salida.cta_salida)
    salida.refresh_from_db()
    return salida


@pytest.fixture
def traspaso_con_cta_entrada_a(traspaso: Movimiento) -> Movimiento:
    dividir_en_dos_subcuentas(traspaso.cta_entrada)
    traspaso.refresh_from_db()
    return traspaso


@pytest.fixture
def traspaso_con_cta_salida_a(traspaso: Movimiento) -> Movimiento:
    dividir_en_dos_subcuentas(traspaso.cta_salida)
    traspaso.refresh_from_db()
    return traspaso


@pytest.fixture
def credito(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Crédito',
        importe=128,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        fecha=fecha,
    )


@pytest.fixture
def donacion(cuenta: CuentaInteractiva, cuenta_ajena: CuentaInteractiva, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Donación',
        importe=253,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        fecha=fecha,
        esgratis=True,
    )


@pytest.fixture
def contramov_credito(credito: Movimiento) -> Movimiento:
    return Movimiento.tomar(id=credito.id_contramov)
