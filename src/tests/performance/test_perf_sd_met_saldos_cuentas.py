from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import SaldoDiario, Cuenta


def test_hace_maximo_2_queries_a_saldodiario(cuenta, cuenta_2, dia):
    with CaptureQueriesContext(connection) as ctx:
        SaldoDiario.saldos_cuentas([cuenta, cuenta_2], dia)

    queries = sum(
        1 for q in ctx.captured_queries if " diario_saldodiario" in q['sql']
    )
    assert queries <= 2


def test_no_genera_n_plus_1_con_multiples_cuentas(
        cuenta, cuenta_2, cuenta_3,
        dia):
    with CaptureQueriesContext(connection) as ctx:
        SaldoDiario.saldos_cuentas([cuenta, cuenta_2, cuenta_3], dia)

    queries = sum(
        1 for q in ctx.captured_queries if "diario_saldodiario" in q['sql']
    )
    assert queries <= 2


def test_queries_no_crece_con_cantidad_de_cuentas_sin_saldo_exacto(dia):
    """Crea muchas cuentas sin SaldoDiario en el día y verifica
    que el método no genere N queries."""
    from diario.models import Titular

    titular = Titular.crear(sk='perf_t', nombre='Perf')
    cuentas = [
        Cuenta.crear(
            nombre=f'cta_perf_{i}',
            sk=f'perf_{i}',
            titular=titular,
        )
        for i in range(10)
    ]

    with CaptureQueriesContext(connection) as ctx:
        SaldoDiario.saldos_cuentas(cuentas, dia)

    queries = sum(
        1 for q in ctx.captured_queries if "diario_saldodiario" in q['sql']
    )
    # Con N+1: 20 queries (10 cuentas × 2 paths)
    # Con batch: <= 2 queries
    assert queries <= 2, f"Hizo {queries} queries con 10 cuentas"


def test_queries_no_explotan_con_cuentas_acumulativas(
        cuenta, cuenta_acumulativa, dia):
    with CaptureQueriesContext(connection) as ctx:
        SaldoDiario.saldos_cuentas(
            [cuenta, cuenta_acumulativa], dia
        )

    queries = sum(
        1 for q in ctx.captured_queries if "diario_saldodiario" in q["sql"]
    )
    # 1 query para interactivas + 1 query para subcuentas de acumulativa
    assert queries <= 3, f"Hizo {queries} queries, esperaba <= 3"


def test_queries_no_explotan_con_movimiento(
        cuenta, dia, entrada, salida):
    with CaptureQueriesContext(connection) as ctx:
        SaldoDiario.saldos_cuentas([cuenta], movimiento=salida)

    queries_sd = sum(
        1 for q in ctx.captured_queries if "diario_saldodiario" in q['sql']
    )
    queries_mov = sum(
        1 for q in ctx.captured_queries if "diario_movimiento" in q['sql']
    )
    assert queries_sd <= 2
    assert queries_mov <= 1
