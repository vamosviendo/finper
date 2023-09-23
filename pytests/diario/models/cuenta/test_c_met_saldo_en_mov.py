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


def test_saldo_de_cuenta_acumulativa_en_mov_en_el_que_era_interactiva_devuelve_saldo_historico_distinto_de_cero(
        cuenta, entrada):
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1 saldo 0', 'sc1', 0],
        ['subcuenta 2 saldo 0', 'sc2'],
    )
    assert cuenta.saldo_en_mov(entrada) != 0


def test_saldo_de_cuenta_acumulativa_en_mov_en_el_que_era_interactiva_devuelve_saldo_historico_correcto(
        cuenta, entrada, salida_posterior):
    saldo_historico = cuenta.saldo_en_mov(entrada)
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1 saldo 0', 'sc1', 0],
        ['subcuenta 2 saldo 0', 'sc2'],
    )
    assert cuenta.saldo_en_mov(entrada) != cuenta.saldo_en_mov(salida_posterior)
    assert cuenta.saldo_en_mov(entrada) == saldo_historico
