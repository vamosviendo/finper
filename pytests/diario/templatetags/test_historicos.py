from diario.templatetags.historicos import cap_historico, saldo_en_moneda
from utils.numeros import float_format


class TestCapHistorico:
    def test_devuelve_string_con_capital_historico_de_titular_al_momento_del_movimiento(
            self, titular, cuenta, entrada, salida_posterior):
        assert cap_historico(titular, entrada) == float_format(titular.capital(entrada))

    def test_si_movimiento_es_None_devuelve_capital_actual_de_titular(
            self, titular, cuenta, entrada, salida_posterior):
        assert cap_historico(titular, None) == float_format(titular.capital())


class TestSaldoHistoricoEnMoneda:
    def test_devuelve_string_con_saldo_de_cuenta_en_movimiento_en_moneda_dada(
            self, cuenta, entrada, salida, dolar):
        assert \
            saldo_en_moneda(cuenta, dolar, entrada) == \
            float_format(cuenta.saldo(movimiento=entrada, moneda=dolar, compra=False))

    def test_si_recibe_movimiento_None_devuelve_saldo_actual_en_moneda_dada(
            self, cuenta_con_saldo, dolar):
        assert \
            saldo_en_moneda(cuenta_con_saldo, dolar, None) == \
            float_format(cuenta_con_saldo.saldo(moneda=dolar, compra=False))
