from datetime import date

import pytest

from diario.models import Titular, Cuenta, CuentaInteractiva, CuentaAcumulativa


@pytest.fixture
def cuenta(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta', slug='c', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_2(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta 2', slug='c2', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_con_saldo(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta_con_saldo', slug='ccs', saldo=100, titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_ajena(otro_titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta ajena',
        slug='caj',
        titular=otro_titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def cuenta_acumulativa(cuenta_con_saldo: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta_con_saldo.dividir_y_actualizar(
        ['subcuenta 1 con saldo', 'scs1', 60],
        ['subcuenta 2 con saldo', 'scs2'],
    )


@pytest.fixture
def cuenta_acumulativa_saldo_0(cuenta: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta.dividir_y_actualizar(
        ['subcuenta 1 saldo 0', 'sc1', 0],
        ['subcuenta 2 saldo 0', 'sc2'],
    )


@pytest.fixture
def cuenta_acumulativa_ajena(cuenta_ajena: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta_ajena.dividir_y_actualizar(
        ['subcuenta 1 ajena', 'sc1', 0],
        ['subcuenta 2 ajena', 'sc2'],
    )


@pytest.fixture
def cuenta_madre_de_cuenta_2(cuenta_2: CuentaInteractiva) -> CuentaAcumulativa:
    return cuenta_2.dividir_y_actualizar(
        ['subcuenta 1 de cuenta 2', 'sc21', 30],
        ['subcuenta 2 de cuenta 2', 'sc22'],
    )
