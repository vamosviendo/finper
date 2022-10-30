from unittest.mock import MagicMock

import pytest

from diario.models import Saldo


@pytest.fixture
def mock_tomar(mocker) -> MagicMock:
    return mocker.patch('diario.models.cuenta.Saldo.tomar')

def test_recupera_saldo_al_momento_del_movimiento(cuenta, entrada, traspaso_posterior, entrada_tardia, mock_tomar):
    cuenta.saldo_en_mov(entrada)
    mock_tomar.assert_called_once_with(cuenta=cuenta, movimiento=entrada)


def test_si_no_encuentra_saldo_de_cuenta_en_fecha_de_mov_devuelve_0(cuenta, entrada, mock_tomar):
    mock_tomar.side_effect = Saldo.DoesNotExist
    assert cuenta.saldo_en_mov(entrada) == 0
