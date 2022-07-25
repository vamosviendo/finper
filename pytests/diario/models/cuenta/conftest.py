from datetime import date

import pytest

from diario.models import Cuenta, Titular, Movimiento


@pytest.fixture
def fecha() -> date:
    return date(2010, 11, 12)


@pytest.fixture
def fecha_posterior() -> date:
    return date(2011, 5, 1)


@pytest.fixture
def cuenta(fecha: date) -> Cuenta:
    return Cuenta.crear(nombre='cuenta', slug='c', fecha_creacion=fecha)


@pytest.fixture
def entrada(cuenta: Cuenta, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Movimiento', importe=100, cta_entrada=cuenta, fecha=fecha
    )


@pytest.fixture
def salida_posterior(cuenta: Cuenta, fecha_posterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Movimiento posterior',
        importe=40,
        cta_salida=cuenta,
        fecha=fecha_posterior
    )


@pytest.fixture
def cuenta_con_saldo(fecha: date) -> Cuenta:
    return Cuenta.crear(nombre='cuenta', slug='c', saldo=100, fecha_creacion=fecha)


@pytest.fixture
def titular() -> Titular:
    return Titular.crear(titname='titular', nombre='Titular')


@pytest.fixture
def otro_titular() -> Titular:
    return Titular.crear(titname='otro', nombre='Otro Titular')
