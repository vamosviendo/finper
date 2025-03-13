import pytest
from diario.templatetags.historicos import cap_historico, saldo_en_moneda
from diario.templatetags.movimientos import movs_seleccionados
from utils.numeros import float_format

pytestmark = pytest.mark.django_db


class TestCapHistorico:
    def test_devuelve_string_con_capital_historico_de_titular_al_momento_del_movimiento(
            self, titular, cuenta, entrada, salida_posterior):
        assert cap_historico(titular, entrada) == float_format(titular.capital_historico(entrada))

    def test_si_movimiento_es_None_devuelve_capital_actual_de_titular(
            self, titular, cuenta, entrada, salida_posterior):
        assert cap_historico(titular, None) == float_format(titular.capital)


class TestSaldoHistoricoEnMoneda:
    def test_devuelve_string_con_saldo_de_cuenta_en_movimiento_en_moneda_dada(
            self, cuenta, entrada, salida, dolar):
        assert \
            saldo_en_moneda(cuenta, dolar, entrada) == \
            float_format(cuenta.saldo(entrada, dolar, compra=False))

    def test_si_recibe_movimiento_None_devuelve_saldo_actual_en_moneda_dada(
            self, cuenta_con_saldo, dolar):
        assert \
            saldo_en_moneda(cuenta_con_saldo, dolar, None) == \
            float_format(cuenta_con_saldo.saldo_en(dolar, compra=False))

class TestFilterMovsSeleccionados:
    def test_devuelve_movimientos_de_una_cuenta_en_un_dia(
            self, dia, cuenta, entrada, salida, entrada_anterior, salida_posterior, entrada_otra_cuenta):
        assert list(movs_seleccionados(dia, cuenta)) == [entrada, salida]

    def test_si_cuenta_es_none_devuelve_todos_los_movimientos_del_dia(
            self, dia, entrada, salida, entrada_anterior, salida_posterior, entrada_otra_cuenta):
        assert list(movs_seleccionados(dia, None)) == [entrada, salida, entrada_otra_cuenta]

    def test_devuelve_movimientos_de_un_titular_en_un_dia(
            self, dia, titular, entrada, salida, entrada_anterior, salida_posterior,
            entrada_otra_cuenta, entrada_cuenta_ajena):
        assert list(movs_seleccionados(dia, titular)) == [entrada, salida, entrada_otra_cuenta]

    def test_si_titular_es_none_devuelve_todos_los_movimientos_del_dia(
            self, dia, titular, entrada, salida, entrada_anterior, salida_posterior,
            entrada_otra_cuenta, entrada_cuenta_ajena):
        assert list(movs_seleccionados(dia, None)) == [entrada, salida, entrada_otra_cuenta, entrada_cuenta_ajena]
