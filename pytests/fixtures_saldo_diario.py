import pytest

from diario.models import CuentaInteractiva, Movimiento, SaldoDiario


@pytest.fixture
def saldo_diario(cuenta: CuentaInteractiva, entrada: Movimiento) -> SaldoDiario:
    assert SaldoDiario.filtro(cuenta=cuenta, dia=entrada.dia).count() == 0
    return SaldoDiario.crear(cuenta=cuenta, dia=entrada.dia, _importe=entrada.importe)


@pytest.fixture
def saldo_diario_anterior(cuenta: CuentaInteractiva, entrada_anterior: Movimiento) -> SaldoDiario:
    assert SaldoDiario.filtro(cuenta=cuenta, dia=entrada_anterior.dia).count() == 0
    return SaldoDiario.crear(cuenta=cuenta, dia=entrada_anterior.dia, importe=entrada_anterior.importe)


@pytest.fixture
def saldo_diario_posterior(cuenta: CuentaInteractiva, salida_posterior: Movimiento) -> SaldoDiario:
    assert SaldoDiario.filtro(cuenta=cuenta, dia=salida_posterior.dia).count() == 0
    return SaldoDiario.crear(cuenta=cuenta, dia=salida_posterior.dia, importe=salida_posterior.importe)
