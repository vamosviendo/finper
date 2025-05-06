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
