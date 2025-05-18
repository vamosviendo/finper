import pytest

from diario.models import CuentaInteractiva, Movimiento, SaldoDiario


@pytest.fixture
def saldo_diario(cuenta: CuentaInteractiva, entrada: Movimiento) -> SaldoDiario:
    return SaldoDiario.tomar(cuenta=cuenta, dia=entrada.dia)


@pytest.fixture
def saldo_diario_anterior(cuenta: CuentaInteractiva, entrada_anterior: Movimiento) -> SaldoDiario:
    return SaldoDiario.tomar(cuenta=cuenta, dia=entrada_anterior.dia)


@pytest.fixture
def saldo_diario_posterior(cuenta: CuentaInteractiva, salida_posterior: Movimiento) -> SaldoDiario:
    return SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)


@pytest.fixture
def saldo_diario_tardio(cuenta: CuentaInteractiva, entrada_tardia: Movimiento) -> SaldoDiario:
    return SaldoDiario.tomar(cuenta=cuenta, dia=entrada_tardia.dia)


@pytest.fixture
def saldo_diario_otra_cuenta(cuenta_2: CuentaInteractiva, entrada_otra_cuenta: Movimiento) -> SaldoDiario:
    return SaldoDiario.tomar(cuenta=cuenta_2, dia=entrada_otra_cuenta.dia)
