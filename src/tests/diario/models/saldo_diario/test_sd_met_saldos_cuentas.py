import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import SaldoDiario, Cuenta


def test_devuelve_dict_con_importes_para_todas_las_cuentas_en_dia_dado(
        cuenta, cuenta_2, dia, saldo_diario, saldo_diario_otra_cuenta):
    resultado = SaldoDiario.saldos_cuentas([cuenta, cuenta_2], dia)

    assert resultado == {
        cuenta.pk: saldo_diario.importe,
        cuenta_2.pk: saldo_diario_otra_cuenta.importe,
    }


def test_devuelve_cero_para_pares_sin_saldo(cuenta, dia):
    resultado = SaldoDiario.saldos_cuentas([cuenta], dia)
    assert resultado == {cuenta.pk: 0.0}


def test_usa_saldo_anterior_si_no_hay_saldo_en_el_dia(
        cuenta, dia_anterior, dia, saldo_diario_anterior):
    resultado = SaldoDiario.saldos_cuentas([cuenta], dia)
    assert resultado == {cuenta.pk: saldo_diario_anterior.importe}


def test_devuelve_saldo_al_momento_de_un_movimiento(cuenta, dia, entrada, salida):
    resultado = SaldoDiario.saldos_cuentas([cuenta], movimiento=entrada)
    assert resultado == {cuenta.pk: cuenta.saldo(movimiento=entrada)}


def test_saldo_en_ultimo_movimiento_del_dia_es_saldo_del_dia(cuenta, dia, entrada, salida):
    resultado = SaldoDiario.saldos_cuentas([cuenta], movimiento=salida)
    saldo_dia = SaldoDiario.saldos_cuentas([cuenta], dia=dia)
    assert resultado == saldo_dia


def test_incluye_saldo_de_cuentas_acumulativas_raiz_con_dia(cuenta, dia, entrada, cuenta_acumulativa):
    resultado = SaldoDiario.saldos_cuentas([cuenta, cuenta_acumulativa], dia)
    assert cuenta_acumulativa.pk in resultado.keys()
    assert resultado[cuenta_acumulativa.pk] == cuenta_acumulativa.saldo()


def test_incluye_saldo_de_cuentas_acumulativas_raiz_con_movimiento(
        cuenta, dia, entrada, cuenta_acumulativa, salida):
    resultado = SaldoDiario.saldos_cuentas([cuenta, cuenta_acumulativa], movimiento=salida)
    assert resultado[cuenta_acumulativa.pk] == cuenta_acumulativa.saldo(movimiento=salida)


# TODO: retirar (redundante). O bien: testear saldo de subsubcuenta
#       en un movimiento anterior al último de subsubcuenta.
def test_incluye_saldo_de_cuenta_acumulativa_anidada_con_dia(
        cuenta, dia, entrada, cuenta_acumulativa, subsubcuenta):
    resultado = SaldoDiario.saldos_cuentas([cuenta, cuenta_acumulativa], dia)
    assert cuenta_acumulativa.pk in resultado.keys()
    assert resultado[cuenta_acumulativa.pk] == cuenta_acumulativa.saldo(dia=dia)


# TODO: retirar (redundante). O bien: testear saldo de subsubcuenta
#       en un movimiento anterior al último de subsubcuenta.
def test_incluye_saldo_de_cuenta_acumulativa_anidada_con_movimiento(
        cuenta, dia, entrada, cuenta_acumulativa, subsubcuenta, salida):
    resultado = SaldoDiario.saldos_cuentas([cuenta, cuenta_acumulativa], movimiento=entrada)
    print("Resultado:", resultado)
    print("Saldo subsubcuenta:", subsubcuenta.saldo(dia=dia))
    assert cuenta_acumulativa.pk in resultado.keys()
    assert resultado[cuenta_acumulativa.pk] == cuenta_acumulativa.saldo(movimiento=entrada)


def test_devuelve_dict_vacio_si_dia_y_movimiento_son_none(cuenta):
    assert SaldoDiario.saldos_cuentas([cuenta]) == {}


def test_si_recibe_dia_y_movimiento_prioriza_movimiento(cuenta, dia, entrada, salida):
    assert cuenta.saldo(movimiento=entrada) != cuenta.saldo(dia=dia)
    saldo = SaldoDiario.saldos_cuentas([cuenta], dia, movimiento=entrada)
    assert saldo[cuenta.pk] == cuenta.saldo(movimiento=entrada)


def test_si_recibe_dia_y_movimiento_de_otro_dia_da_valueerror(cuenta, dia, salida_posterior):
    with pytest.raises(
            ValueError,
            match=
                f'El movimiento "{salida_posterior.concepto}" del '
                f'{salida_posterior.dia} no corresponde al día {dia}.'
    ):
        SaldoDiario.saldos_cuentas([cuenta], dia, movimiento=salida_posterior)


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
