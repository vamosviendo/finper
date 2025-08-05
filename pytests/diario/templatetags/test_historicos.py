from diario.templatetags.historicos import cap_historico, saldo_en_moneda, saldo
from diario.utils.utils_saldo import saldo_general_historico
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


class TestSaldo:
    def test_devuelve_saldo_general(self, entrada, salida, salida_posterior):
        assert saldo() == salida_posterior.dia.saldo()

    def test_si_recibe_dia_devuelve_saldo_general_al_dia_recibido(self, dia, entrada, salida, salida_posterior):
        assert saldo(dia=dia) == dia.saldo()

    def test_si_recibe_movimiento_devuelve_saldo_general_al_momento_del_movimiento(
            self, entrada, salida, salida_posterior):
        assert saldo(movimiento=entrada) == saldo_general_historico(entrada)

    def test_si_recibe_dia_y_movimiento_prioriza_movimiento(self, entrada, salida, salida_posterior):
        assert saldo(dia=salida_posterior.dia, movimiento=entrada) == saldo_general_historico(entrada)

    def test_si_recibe_moneda_devuelve_saldo_general_en_moneda_recibida(
            self, entrada, salida, salida_posterior, dolar):
        hoy = salida_posterior.dia
        assert saldo(moneda=dolar) == round(hoy.saldo() / dolar.cotizacion_al(hoy.fecha, compra=False), 2)

    def test_si_recibe_cuenta_devuelve_saldo_de_la_cuenta(
            self, cuenta, entrada, entrada_otra_cuenta, salida_posterior):
        assert saldo(cuenta=cuenta) == cuenta.saldo()

    def test_si_recibe_cuenta_y_dia_devuelve_saldo_de_la_cuenta_al_dia_recibido(
            self, cuenta, dia, entrada, entrada_otra_cuenta, salida_posterior):
        assert saldo(cuenta=cuenta, dia=dia) == cuenta.saldo(dia=dia)

    def test_si_recibe_cuenta_y_movimiento_devuelve_saldo_de_la_cuenta_al_momento_del_movimiento(
            self, cuenta, entrada, salida, entrada_otra_cuenta, salida_posterior):
        assert saldo(cuenta=cuenta, movimiento=entrada) == cuenta.saldo(movimiento=entrada)

    def test_si_recibe_cuenta_y_moneda_devuelve_saldo_de_cuenta_en_moneda_recibida(
            self, cuenta, entrada, entrada_otra_cuenta, salida_posterior, dolar):
        assert saldo(cuenta=cuenta, moneda=dolar) == cuenta.saldo(moneda=dolar)

    def test_si_recibe_cuenta_y_no_moneda_devuelve_saldo_en_moneda_de_la_cuenta(
            self, dolar, cuenta_en_dolares, entrada_en_dolares, salida_en_dolares):
        assert saldo(cuenta=cuenta_en_dolares) == cuenta_en_dolares.saldo(moneda=dolar)

    def test_si_recibe_titular_devuelve_capital_del_titular(
            self, titular, entrada, entrada_cuenta_ajena, salida_posterior):
        assert saldo(titular=titular) == titular.capital()

    def test_si_recibe_titular_y_dia_devuelve_capital_del_titular_al_dia_recibido(
            self, dia, titular, entrada, entrada_cuenta_ajena, salida_posterior):
        assert saldo(titular=titular, dia=dia) == titular.capital(dia=dia)

    def test_si_recibe_titular_y_movimiento_devuelve_capital_del_titular_al_momento_del_movimiento(
            self, titular, entrada, salida, entrada_cuenta_ajena, salida_posterior):
        assert saldo(titular=titular, movimiento=entrada) == titular.capital(movimiento=entrada)

    def test_si_recibe_titular_y_cuenta_prioriza_cuenta(
            self, titular, cuenta_ajena, entrada, salida, entrada_cuenta_ajena, entrada_posterior_cuenta_ajena):
        assert saldo(titular=titular, cuenta=cuenta_ajena) == cuenta_ajena.saldo()

    def test_si_recibe_titular_y_moneda_devuelve_capital_en_moneda_recibida(
            self, titular, entrada, salida, salida_posterior, dolar):
        assert saldo(titular=titular, moneda=dolar) == round(titular.capital() / dolar.cotizacion, 2)
