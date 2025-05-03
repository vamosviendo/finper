import pytest

from diario.models import CuentaInteractiva, Movimiento, SaldoDiario


@pytest.fixture
def saldo_diario(cuenta: CuentaInteractiva, entrada: Movimiento) -> SaldoDiario:
    return SaldoDiario.crear(cuenta=cuenta, dia=entrada.dia, _importe=entrada.importe)
