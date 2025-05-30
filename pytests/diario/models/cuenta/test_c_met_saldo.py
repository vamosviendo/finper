from unittest.mock import MagicMock

import pytest

from diario.models import Saldo


@pytest.fixture
def mock_tomar(mocker) -> MagicMock:
    return mocker.patch('diario.models.cuenta.SaldoDiario.tomar')


@pytest.fixture
def mock_saldo_en_mov(mocker) -> MagicMock:
    return mocker.patch('diario.models.cuenta.Cuenta.saldo_en_mov', autospec=True)


def test_devuelve_el_ultimo_saldo_historico_de_la_cuenta(cuenta, entrada, salida_posterior):
    assert (
        cuenta.saldo() ==
        Saldo.objects.get(cuenta=cuenta, movimiento=salida_posterior).importe
    )


def test_si_no_encuentra_saldos_en_la_cuenta_devuelve_cero(cuenta):
    # No hay movimientos, por lo tanto no hay saldos
    assert cuenta.saldo() == 0.0


def test_si_recibe_movimiento_recupera_saldo_al_momento_del_movimiento(
        cuenta, entrada, traspaso_posterior, entrada_tardia, mock_saldo_en_mov):
    cuenta.saldo(movimiento=entrada)
    mock_saldo_en_mov.assert_called_once_with(cuenta, movimiento=entrada)


def test_si_no_encuentra_saldo_de_cuenta_en_movimiento_devuelve_saldo_en_movimiento_anterior(
        cuenta, entrada, entrada_posterior_otra_cuenta):
    assert cuenta.saldo(movimiento=entrada_posterior_otra_cuenta) == cuenta.saldo(movimiento=entrada)


def test_si_recibe_movimiento_y_cuenta_no_tiene_saldos_devuelve_cero(cuenta, entrada_otra_cuenta):
    assert cuenta.saldo(movimiento=entrada_otra_cuenta) == 0

@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_si_recibe_moneda_devuelve_saldo_en_moneda_dada_redondeado_en_2_decimales(
        tipo, cuenta_con_saldo, peso, dolar):
    compra = tipo == "compra"
    assert \
        cuenta_con_saldo.saldo(moneda=dolar, compra=compra) == \
        round(cuenta_con_saldo.saldo() * cuenta_con_saldo.moneda.cotizacion_en(dolar, compra=compra), 2)
    assert cuenta_con_saldo.saldo(moneda=peso, compra=compra) == cuenta_con_saldo.saldo()

@pytest.mark.parametrize("fixture_mov", ["entrada", "salida"])
@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_si_recibe_moneda_y_movimiento_devuelve_saldo_en_movimiento_dado_en_moneda_dada_a_la_fecha_del_movimiento_redondeado_en_2_decimales(
        fixture_mov, tipo, cuenta, peso, dolar, request):
    mov = request.getfixturevalue(fixture_mov)
    request.getfixturevalue("salida_posterior")
    compra = tipo == "compra"
    assert \
        cuenta.saldo(mov, dolar, compra) == \
        round(cuenta.saldo(movimiento=mov) * cuenta.moneda.cotizacion_en_al(dolar, fecha=mov.fecha, compra=compra), 2)
    assert cuenta.saldo(mov, peso, compra) == cuenta.saldo(movimiento=mov)
