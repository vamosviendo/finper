from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import Cuenta, CuentaInteractiva, Moneda, Titular
from diario.utils.utils_saldo import precalcular_saldos_cuentas


def queries_a_tabla(queries, tabla):
    return sum(1 for q in queries if tabla in q["sql"])


@pytest.fixture
def cuenta_con_saldo_en_dolares_2(
        titular: Titular,
        fecha_temprana: date,
        dolar: Moneda) -> CuentaInteractiva:
    return Cuenta.crear(
        nombre='cuenta con saldo en dólares 2',
        sk='ccsd2',
        saldo=200,
        titular=titular,
        fecha_creacion=fecha_temprana,
        moneda=dolar,
    )


class TestPrecalcularSaldosCuentasPorDiaPerformance:
    def test_con_una_cuenta_hace_una_sola_query_a_saldo_diario(
            self, cuenta, entrada, peso):
        dia = entrada.dia
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta], [peso], dia=dia)

        assert queries_a_tabla(ctx.captured_queries, "diario_saldodiario") == 1

    def test_con_multiples_cuentas_hace_una_sola_query_a_saldo_diario(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta, peso):
        dia = entrada.dia
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta, cuenta_2], [peso], dia=dia)

        assert queries_a_tabla(ctx.captured_queries, "diario_saldodiario") == 1

    def test_con_multiples_cuentas_sin_saldo_en_dia_exacto_hace_dos_queries_a_saldo_diario(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta, dia_posterior, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta, cuenta_2], [peso], dia=dia_posterior)

        assert queries_a_tabla(ctx.captured_queries, "diario_saldodiario") == 2

    def test_numero_de_queries_no_crece_con_cantidad_de_cuentas(
            self, cuenta, cuenta_2, cuenta_3, entrada, entrada_otra_cuenta,
            salida_tardia_tercera_cuenta, dia_posterior, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas(
                [cuenta, cuenta_2, cuenta_3],
                [peso],
                dia=dia_posterior
            )
        assert queries_a_tabla(ctx.captured_queries, "diario_saldodiario") == 2


class TestPrecalcularSaldosCuentasPorMovimientoPerformance:

    def test_con_una_cuenta_hace_una_sola_query_a_saldo_diario(
            self, cuenta, entrada, salida, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta], [peso], movimiento=entrada)
        assert queries_a_tabla(ctx.captured_queries, "diario_saldodiario") == 1

    def test_con_multiples_cuentas_hace_una_sola_query_a_saldo_diario(
            self, cuenta, cuenta_2, entrada, entrada_otra_cuenta, peso):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas([cuenta, cuenta_2], [peso], movimiento=entrada)
        assert queries_a_tabla(ctx.captured_queries, "diario_saldodiario") == 1

class TestPrecalcularSaldosCuentasCotizacionesPerformance:
    def test_con_multiples_cuentas_en_la_misma_moneda_no_repite_query_de_cotizacion(
            self, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_dolares_2,
            peso, dolar, dia):
        with CaptureQueriesContext(connection) as ctx:
            precalcular_saldos_cuentas(
                [cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_dolares_2],
                [peso], dia=dia
            )

        assert queries_a_tabla(ctx.captured_queries, "diario_cotizacion") == 1
    #
    # def test_numero_de_queries_de_cotizacion_es_igual_al_numero_de_pares_de_monedas_distintas(
    #         self, cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros,
    #         peso, dolar, euro, dia):
    #     with CaptureQueriesContext(connection) as ctx:
    #         precalcular_saldos_cuentas(
    #             [cuenta_con_saldo_en_dolares, cuenta_con_saldo_en_euros],
    #             [peso], dia=dia
    #         )
    #     assert queries_a_tabla(ctx.captured_queries, "diario_cotizacion") == 2