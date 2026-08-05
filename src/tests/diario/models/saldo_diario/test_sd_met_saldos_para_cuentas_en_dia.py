from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import SaldoDiario, Cuenta


def test_devuelve_dict_con_importes_para_todas_las_cuentas_en_dia_dado(
        cuenta, cuenta_2, dia, saldo_diario, saldo_diario_otra_cuenta):
    resultado = SaldoDiario.saldos_para_cuentas_en_dia([cuenta, cuenta_2], dia)

    assert resultado == {
        cuenta.pk: saldo_diario.importe,
        cuenta_2.pk: saldo_diario_otra_cuenta.importe,
    }


def test_devuelve_cero_para_pares_sin_saldo(cuenta, dia):
    resultado = SaldoDiario.saldos_para_cuentas_en_dia([cuenta], dia)
    assert resultado == {cuenta.pk: 0.0}


def test_usa_saldo_anterior_si_no_hay_saldo_en_el_dia(
        cuenta, dia_anterior, dia, saldo_diario_anterior):
    resultado = SaldoDiario.saldos_para_cuentas_en_dia([cuenta], dia)
    assert resultado == {cuenta.pk: saldo_diario_anterior.importe}


def test_hace_maximo_2_queries_a_saldodiario(cuenta, cuenta_2, dia):
    with CaptureQueriesContext(connection) as ctx:
        SaldoDiario.saldos_para_cuentas_en_dia([cuenta, cuenta_2], dia)

    queries = sum(
        1 for q in ctx.captured_queries if " diario_saldodiario" in q['sql']
    )
    assert queries <= 2


def test_no_genera_n_plus_1_con_multiples_cuentas(
        cuenta, cuenta_2, cuenta_3,
        dia):
    with CaptureQueriesContext(connection) as ctx:
        SaldoDiario.saldos_para_cuentas_en_dia([cuenta, cuenta_2, cuenta_3], dia)

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
        SaldoDiario.saldos_para_cuentas_en_dia(cuentas, dia)

    queries = sum(
        1 for q in ctx.captured_queries if "diario_saldodiario" in q['sql']
    )
    # Con N+1: 20 queries (10 cuentas × 2 paths)
    # Con batch: <= 2 queries
    assert queries <= 2, f"Hizo {queries} queries con 10 cuentas"
