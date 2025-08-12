from diario.templatetags.historicos import saldo_en_moneda, saldo
from diario.utils.utils_saldo import saldo_general_historico
from pytests.fixtures_movimiento import entrada_cuenta_ajena
from utils.numeros import float_format


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
        context = dict()
        assert saldo(context) == float_format(salida_posterior.dia.saldo())

    def test_si_recibe_dia_en_context_devuelve_saldo_general_al_dia_recibido(self, dia, entrada, salida, salida_posterior):
        context = {"dia": dia}
        assert saldo(context) == float_format(dia.saldo())

    def test_si_recibe_movimiento_en_context_devuelve_saldo_general_al_momento_del_movimiento(
            self, entrada, salida, salida_posterior):
        context = {"movimiento": entrada}
        assert saldo(context) == float_format(saldo_general_historico(entrada))

    def test_si_recibe_dia_y_movimiento_en_context_prioriza_movimiento(self, entrada, salida, salida_posterior):
        context = {"dia": salida_posterior.dia, "movimiento": entrada}
        assert saldo(context) == float_format(saldo_general_historico(entrada))

    def test_si_recibe_moneda_devuelve_saldo_general_en_moneda_recibida(
            self, entrada, salida, salida_posterior, dolar):
        context = dict()
        hoy = salida_posterior.dia
        assert saldo(context, moneda=dolar) == float_format(hoy.saldo() / dolar.cotizacion_al(hoy.fecha, compra=False))

    def test_si_recibe_cuenta_en_context_devuelve_saldo_de_la_cuenta(
            self, cuenta, entrada, entrada_otra_cuenta, salida_posterior):
        context = {"cuenta": cuenta}
        assert saldo(context) == float_format(cuenta.saldo())

    def test_si_recibe_cuenta_y_dia_en_context_devuelve_saldo_de_la_cuenta_al_dia_recibido(
            self, cuenta, dia, entrada, entrada_otra_cuenta, salida_posterior):
        context = {"cuenta": cuenta, "dia": dia}
        assert saldo(context) == float_format(cuenta.saldo(dia=dia))

    def test_si_recibe_cuenta_y_movimiento_en_context_devuelve_saldo_de_la_cuenta_al_momento_del_movimiento(
            self, cuenta, entrada, salida, entrada_otra_cuenta, salida_posterior):
        context = {"cuenta": cuenta, "movimiento": entrada}
        assert saldo(context) == float_format(cuenta.saldo(movimiento=entrada))

    def test_si_recibe_cuenta_en_context_y_moneda_devuelve_saldo_de_cuenta_en_moneda_recibida(
            self, cuenta, entrada, entrada_otra_cuenta, salida_posterior, dolar):
        context = {"cuenta": cuenta}
        assert saldo(context, moneda=dolar) == float_format(cuenta.saldo(moneda=dolar))

    def test_si_recibe_cuenta_en_context_y_no_recibe_moneda_devuelve_saldo_en_moneda_de_la_cuenta(
            self, dolar, cuenta_en_dolares, entrada_en_dolares, salida_en_dolares):
        context = {"cuenta": cuenta_en_dolares}
        assert saldo(context) == float_format(cuenta_en_dolares.saldo(moneda=dolar))

    def test_si_recibe_cuenta_en_context_y_como_argumento_prioriza_argumento(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta):
        context = {"cuenta": cuenta}
        assert saldo(context, cuenta=cuenta_2) == float_format(cuenta_2.saldo())

    def test_si_recibe_titular_en_context_devuelve_capital_del_titular(
            self, titular, entrada, entrada_cuenta_ajena, salida_posterior):
        context = {"titular": titular}
        assert saldo(context) == float_format(titular.capital())

    def test_si_recibe_titular_y_dia_en_context_devuelve_capital_del_titular_al_dia_recibido(
            self, dia, titular, entrada, entrada_cuenta_ajena, salida_posterior):
        context = {"titular": titular, "dia": dia}
        assert saldo(context) == float_format(titular.capital(dia=dia))

    def test_si_recibe_titular_y_movimiento_en_context_devuelve_capital_del_titular_al_momento_del_movimiento(
            self, titular, entrada, salida, entrada_cuenta_ajena, salida_posterior):
        context = {"titular": titular, "movimiento": entrada}
        assert saldo(context) == float_format(titular.capital(movimiento=entrada))

    def test_si_recibe_titular_y_cuenta_en_context_prioriza_cuenta(
            self, titular, cuenta_ajena, entrada, salida, entrada_cuenta_ajena, entrada_posterior_cuenta_ajena):
        context = {"titular": titular, "cuenta": cuenta_ajena}
        assert saldo(context) == float_format(cuenta_ajena.saldo())

    def test_si_recibe_titular_en_context_y_moneda_devuelve_capital_en_moneda_recibida(
            self, titular, entrada, salida, salida_posterior, dolar):
        context = {"titular": titular}
        assert saldo(context, moneda=dolar) == float_format(titular.capital() / dolar.cotizacion)

    def test_si_recibe_titular_en_context_y_como_argumento_prioriza_argumento(
            self, titular, otro_titular, entrada, entrada_cuenta_ajena):
        context = {"titular": titular}
        assert saldo(context, titular=otro_titular) == float_format(otro_titular.capital())

    def test_si_recibe_cuenta_en_context_y_titular_como_argumento_prioriza_titular(
            self, cuenta, titular, otro_titular, entrada, entrada_otra_cuenta, entrada_cuenta_ajena):
        context = {"cuenta": cuenta, "titular": titular}
        assert saldo(context, titular=otro_titular) == float_format(otro_titular.capital())

    def test_si_no_hay_dias_ni_movimientos_devuelve_cero(self):
        context = dict()
        assert saldo(context) == "0,00"
