from datetime import date

import pytest

from diario.models import Titular, CuentaInteractiva, Cuenta


@pytest.fixture
def cuenta(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta', slug='c', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_2(titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta 2', slug='c2', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_con_saldo(fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta', slug='c', saldo=100, fecha_creacion=fecha)


@pytest.fixture
def cuenta_ajena(otro_titular: Titular, fecha: date) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta ajena',
        slug='caj',
        titular=otro_titular,
        fecha_creacion=fecha
    )
