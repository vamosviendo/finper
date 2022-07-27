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
def fecha_tardia() -> date:
    return date(2015, 6, 20)


@pytest.fixture
def fecha_tardia_plus() -> date:
    return date(2017, 3, 14)


@pytest.fixture
def cuenta(titular: Titular, fecha: date) -> Cuenta:
    return Cuenta.crear(
        nombre='cuenta', slug='c', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_2(titular: Titular, fecha: date) -> Cuenta:
    return Cuenta.crear(
        nombre='cuenta 2', slug='c2', titular=titular, fecha_creacion=fecha)


@pytest.fixture
def cuenta_ajena(otro_titular: Titular, fecha: date) -> Cuenta:
    return Cuenta.crear(
        nombre='cuenta ajena',
        slug='caj',
        titular=otro_titular,
        fecha_creacion=fecha
    )


@pytest.fixture
def entrada(cuenta: Cuenta, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada', importe=100, cta_entrada=cuenta, fecha=fecha
    )


@pytest.fixture
def entrada_tardia(cuenta: Cuenta, fecha_tardia: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada tardía', importe=80, cta_entrada=cuenta, fecha=fecha_tardia
    )


@pytest.fixture
def entrada_posterior_otra_cuenta(cuenta_2: Cuenta, fecha_posterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Entrada posterior otra cuenta', importe=50,
        cta_entrada=cuenta_2, fecha=fecha_posterior
    )


@pytest.fixture
def salida_posterior(cuenta: Cuenta, fecha_posterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Salida posterior',
        importe=40,
        cta_salida=cuenta,
        fecha=fecha_posterior
    )


@pytest.fixture
def traspaso_posterior(cuenta: Cuenta, cuenta_2: Cuenta, fecha_posterior: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Traspaso posterior', importe=70,
        cta_entrada=cuenta_2, cta_salida=cuenta,
        fecha=fecha_posterior,
    )


@pytest.fixture
def credito(cuenta: Cuenta, cuenta_ajena: Cuenta, fecha: date) -> Movimiento:
    return Movimiento.crear(
        concepto='Crédito',
        importe=100,
        cta_entrada=cuenta,
        cta_salida=cuenta_ajena,
        fecha=fecha,
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
