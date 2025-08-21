from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_tomar(mocker) -> MagicMock:
    return mocker.patch('diario.models.cuenta.SaldoDiario.tomar')


@pytest.fixture
def mock_saldo_en_mov(mocker) -> MagicMock:
    return mocker.patch('diario.models.cuenta.Cuenta.saldo_en_mov', autospec=True)


def test_devuelve_el_ultimo_saldo_historico_de_la_cuenta(cuenta, entrada, salida_posterior):
    assert (
        cuenta.saldo() == cuenta.saldodiario_set.last().importe
    )


def test_si_no_encuentra_saldos_en_la_cuenta_devuelve_cero(cuenta):
    # No hay movimientos, por lo tanto no hay saldos
    assert cuenta.saldo() == 0.0


def test_si_recibe_movimiento_recupera_saldo_al_momento_del_movimiento(
        cuenta, entrada, traspaso_posterior, entrada_tardia, mock_saldo_en_mov):
    cuenta.saldo(movimiento=entrada)
    mock_saldo_en_mov.assert_called_once_with(cuenta, movimiento=entrada)


def test_si_recibe_movimiento_devuelve_saldo_al_momento_del_movimiento(cuenta, entrada, traspaso_posterior):
    assert cuenta.saldo(movimiento=entrada) == cuenta.saldo_en_mov(entrada)


def test_si_no_encuentra_saldo_de_cuenta_en_movimiento_devuelve_saldo_en_movimiento_anterior(
        cuenta, entrada, entrada_posterior_otra_cuenta):
    assert cuenta.saldo(movimiento=entrada_posterior_otra_cuenta) == cuenta.saldo(movimiento=entrada)


def test_si_recibe_movimiento_y_cuenta_no_tiene_saldos_devuelve_cero(cuenta, entrada_otra_cuenta):
    assert cuenta.saldo(movimiento=entrada_otra_cuenta) == 0


def test_si_recibe_dia_devuelve_saldo_diario_del_dia(cuenta, entrada, salida, salida_posterior, dia):
    assert cuenta.saldo(dia=dia) == cuenta.saldodiario_set.get(dia=dia).importe


def test_si_recibe_dia_y_movimiento_devuelve_saldo_al_momento_del_movimiento(
        cuenta, entrada, salida, salida_posterior, dia):
    assert cuenta.saldo(dia=dia, movimiento=entrada) == cuenta.saldo_en_mov(entrada)


def test_si_recibe_dia_y_movimiento_de_otro_dia_da_error(cuenta, entrada, salida, salida_posterior, dia):
    with pytest.raises(ValueError):
        cuenta.saldo(dia=dia, movimiento=salida_posterior)


def test_si_recibe_dia_sin_saldo_diario_devuelve_importe_de_saldo_diario_anterior(
        cuenta, entrada, salida, dia, dia_posterior):
    assert cuenta.saldo(dia=dia_posterior) == cuenta.saldodiario_set.get(dia=dia).importe


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_si_recibe_moneda_devuelve_saldo_en_moneda_dada_redondeado_en_2_decimales(
        tipo, cuenta_con_saldo, peso, dolar):
    compra = tipo == "compra"
    assert \
        cuenta_con_saldo.saldo(moneda=dolar, compra=compra) == \
        round(cuenta_con_saldo.saldo() * cuenta_con_saldo.moneda.cotizacion_en(dolar, compra=compra), 2)
    assert cuenta_con_saldo.saldo(moneda=peso, compra=compra) == cuenta_con_saldo.saldo()


def test_si_moneda_recibida_no_tiene_cotizaciones_asociadas_devuelve_saldo_en_moneda_de_la_cuenta(
        cuenta_con_saldo, peso, dolar):
    dolar.cotizaciones.all().delete()
    assert cuenta_con_saldo.saldo(moneda=dolar) == cuenta_con_saldo.saldo()


@pytest.mark.parametrize("fixture_mov", ["entrada", "salida"])
@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_si_recibe_moneda_y_movimiento_devuelve_saldo_en_movimiento_dado_en_moneda_dada_a_la_fecha_del_movimiento_redondeado_en_2_decimales(
        fixture_mov, tipo, cuenta, peso, dolar, request):
    mov = request.getfixturevalue(fixture_mov)
    request.getfixturevalue("salida_posterior")
    compra = tipo == "compra"
    assert \
        cuenta.saldo(movimiento=mov, moneda=dolar, compra=compra) == \
        round(cuenta.saldo(movimiento=mov) * cuenta.moneda.cotizacion_en_al(dolar, fecha=mov.fecha, compra=compra), 2)
    assert cuenta.saldo(movimiento=mov, moneda=peso, compra=compra) == cuenta.saldo(movimiento=mov)

@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_si_recibe_moneda_y_dia_devuelve_saldo_en_dia_dado_en_moneda_dada_a_la_fecha_del_dia_redondeado_en_2_decimales(
        entrada, salida, dia, tipo, cuenta, peso, dolar, request):
    request.getfixturevalue("salida_posterior")
    compra = tipo == "compra"
    assert \
        cuenta.saldo(dia=dia, moneda=dolar, compra=compra) == \
        round(cuenta.saldo(dia=dia) * cuenta.moneda.cotizacion_en_al(dolar, fecha=dia.fecha, compra=compra), 2)
    assert cuenta.saldo(dia=dia, moneda=peso, compra=compra) == cuenta.saldo(dia=dia)
