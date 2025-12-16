from unittest.mock import MagicMock

import pytest

from diario.utils.utils_saldo import verificar_saldos


# Fixtures

@pytest.fixture
def mock_saldo_ok(mocker) -> MagicMock:
    return mocker.patch('diario.models.CuentaInteractiva.saldo_ok')


# Tests

def test_devuelve_lista_vacia_si_todos_los_saldos_ok(
        cuenta, cuenta_con_saldo, cuenta_con_saldo_negativo, mock_saldo_ok):
    mock_saldo_ok.return_value = True
    ctas_erroneas = verificar_saldos()
    assert ctas_erroneas == []


def test_devuelve_lista_de_cuentas_con_saldos_incorrectos(
        cuenta, cuenta_con_saldo, cuenta_con_saldo_negativo, mock_saldo_ok):
    mock_saldo_ok.side_effect = [False, False, True]
    ctas_erroneas = verificar_saldos()
    assert cuenta in ctas_erroneas
    assert cuenta_con_saldo in ctas_erroneas
    assert cuenta_con_saldo_negativo not in ctas_erroneas
