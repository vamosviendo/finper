from datetime import date

import pytest

from diario.models import Cuenta, Titular, Movimiento, Saldo, CuentaInteractiva


@pytest.fixture
def fecha_anterior() -> date:
    return date(2010, 9, 10)


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
def saldo_anterior(entrada_anterior: Movimiento) -> Saldo:
    return entrada_anterior.saldo_ce()


@pytest.fixture
def saldo(entrada: Movimiento) -> Saldo:
    return entrada.saldo_ce()


@pytest.fixture
def saldo_salida(salida: Movimiento) -> Saldo:
    return salida.saldo_cs()


@pytest.fixture
def saldo_traspaso_cuenta(traspaso: Movimiento) -> Saldo:
    return traspaso.saldo_ce()


@pytest.fixture
def saldo_traspaso_cuenta2(traspaso: Movimiento) -> Saldo:
    return traspaso.saldo_cs()


@pytest.fixture
def saldo_posterior(traspaso_posterior: Movimiento) -> Saldo:
    return traspaso_posterior.saldo_cs()


@pytest.fixture
def saldo_tardio(entrada_tardia: Movimiento) -> Saldo:
    return entrada_tardia.saldo_ce()


@pytest.fixture
def saldo_cuenta_2(traspaso: Movimiento) -> Saldo:
    return traspaso.saldo_cs()


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
def titular() -> Titular:
    return Titular.crear(titname='titular', nombre='Titular')


@pytest.fixture
def otro_titular() -> Titular:
    return Titular.crear(titname='otro', nombre='Otro Titular')
