from unittest.mock import MagicMock

import pytest

from diario.models import Saldo


@pytest.fixture
def mock_tomar(mocker) -> MagicMock:
    return mocker.patch('diario.models.cuenta.Saldo.tomar')


def test_devuelve_el_ultimo_saldo_historico_de_la_cuenta(cuenta, entrada, salida_posterior):
    assert (
        cuenta.saldo() ==
        Saldo.objects.get(cuenta=cuenta, movimiento=salida_posterior).importe
    )


def test_si_no_encuentra_saldos_en_la_cuenta_devuelve_cero(cuenta):
    # No hay movimientos, por lo tanto no hay saldos
    assert cuenta.saldo() == 0.0


def test_si_recibe_movimiento_recupera_saldo_al_momento_del_movimiento(
        cuenta, entrada, traspaso_posterior, entrada_tardia, mock_tomar):
    cuenta.saldo(movimiento=entrada)
    mock_tomar.assert_called_once_with(cuenta=cuenta, movimiento=entrada)


def test_si_no_encuentra_saldo_de_cuenta_en_movimiento_devuelve_saldo_en_movimiento_anterior(
        cuenta, entrada, entrada_posterior_otra_cuenta):
    assert cuenta.saldo(movimiento=entrada_posterior_otra_cuenta) == cuenta.saldo(movimiento=entrada)


def test_si_recibe_movimiento_y_cuenta_no_tiene_saldos_devuelve_cero(cuenta, entrada_otra_cuenta):
    assert cuenta.saldo(movimiento=entrada_otra_cuenta) == 0
