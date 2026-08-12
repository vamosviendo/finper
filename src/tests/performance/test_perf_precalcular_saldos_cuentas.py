from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.utils.utils_saldo import precalcular_saldos_cuentas


def _contar(queries, tabla):
    return sum(1 for q in queries if tabla in q["sql"])


class TestPrecalcularSaldosCuentasPorDiaPerformance:
    def test_con_una_cuenta_hace_una_sola_query_a_saldo_diario(
            self, cuenta, entrada, peso):
        dia = entrada.dia
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta], [peso], dia=dia)

        assert _contar(ctx.captured_queries, "diario_saldodiario") == 1

    def test_con_multiples_cuentas_hace_una_sola_query_a_saldo_diario(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta, peso):
        dia = entrada.dia
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta, cuenta_2], [peso], dia=dia)

        assert _contar(ctx.captured_queries, "diario_saldodiario") == 1

    def test_con_multiples_cuentas_sin_saldo_en_dia_exacto_hace_un_query_a_saldo_diario(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta, dia_posterior, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta, cuenta_2], [peso], dia=dia_posterior)

        assert _contar(ctx.captured_queries, "diario_saldodiario") == 1

    def test_numero_de_queries_no_crece_con_cantidad_de_cuentas(
            self, cuenta, cuenta_2, cuenta_3, entrada, entrada_otra_cuenta,
            salida_tardia_tercera_cuenta, dia_posterior, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas(
                [cuenta, cuenta_2, cuenta_3],
                [peso],
                dia=dia_posterior
            )
        assert _contar(ctx.captured_queries, "diario_saldodiario") == 1


class TestPrecalcularSaldosCuentasPorMovimientoPerformance:

    def test_con_una_cuenta_hace_una_sola_query_a_saldo_diario(
            self, cuenta, entrada, salida, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta], [peso], movimiento=entrada)
        assert _contar(ctx.captured_queries, "diario_saldodiario") == 1

    def test_con_multiples_cuentas_hace_una_sola_query_a_saldo_diario(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta, cuenta_2], [peso], movimiento=entrada)
        assert _contar(ctx.captured_queries, "diario_saldodiario") == 1

    def test_numero_de_queries_no_crece_con_cantidad_de_cuentas(
            self, cuenta, cuenta_2, cuenta_3, entrada, entrada_otra_cuenta,
            entrada_tercera_cuenta, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta, cuenta_2, cuenta_3], [peso], movimiento=entrada)
        assert _contar(ctx.captured_queries, "diario_saldodiario") == 1

    def test_con_multiples_cuentas_sin_saldo_en_dia_del_movimiento_hace_un_query_a_saldo_diario(
            self, cuenta, cuenta_2, cuenta_3, entrada, entrada_otra_cuenta,
            salida_tardia_tercera_cuenta, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta, cuenta_2, cuenta_3], [peso], movimiento=entrada)
        assert _contar(ctx.captured_queries, "diario_saldodiario") == 1

    def test_no_genera_n_plus_1_con_acumulativas(
            self, cuenta, cuenta_2, cuenta_acumulativa, dia, entrada, salida, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas(
                [cuenta, cuenta_acumulativa], [peso], movimiento=salida
            )
            queries_saldos = _contar(ctx.captured_queries, "diario_saldodiario")
            queries_cuenta = _contar(ctx.captured_queries, "diario_cuenta")
            assert queries_saldos <= 3, f"Hizo {queries_saldos} queries a saldodiario"
            assert queries_cuenta <= 5, f"Hizo {queries_cuenta} queries a cuenta, posible N+1"


class TestPrecalcularSaldosCuentasCotizacionesPerformance:
    def test_con_multiples_cuentas_en_la_misma_moneda_no_repite_query_de_cotizacion(
            self, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_dolares_2,
            peso, dolar, dia):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas(
                [cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_dolares_2],
                [peso], dia=dia
            )

        assert _contar(ctx.captured_queries, "diario_cotizacion") == 1

    def test_numero_de_queries_de_cotizacion_no_crece_con_cantidad_de_cuentas(
            self, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_dolares_2,
            peso, dolar, dia):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas(
                [cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_dolares_2],
                [peso], dia=dia
            )
        assert _contar(ctx.captured_queries, "diario_cotizacion") == 1
