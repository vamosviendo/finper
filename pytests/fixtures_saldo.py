import pytest

from diario.models import Movimiento, Saldo


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
