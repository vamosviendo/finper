from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import Movimiento
from diario.utils.utils_saldo import saldo_general_historico
from utils.helpers_tests import dividir_en_dos_subcuentas


def test_si_recibe_movimiento_devuelve_suma_de_saldos_historicos_de_cuentas_al_momento_del_movimiento(
        entrada, salida, entrada_posterior_otra_cuenta, salida_tardia_tercera_cuenta):
    assert \
        saldo_general_historico(entrada) == \
        entrada.cta_entrada.saldo(movimiento=entrada)
    assert \
        saldo_general_historico(entrada_posterior_otra_cuenta) == \
            entrada.cta_entrada.saldo(movimiento=entrada_posterior_otra_cuenta) + \
            entrada_posterior_otra_cuenta.cta_entrada.saldo(movimiento=entrada_posterior_otra_cuenta)
    assert \
        saldo_general_historico(salida_tardia_tercera_cuenta) == \
            saldo_general_historico(entrada_posterior_otra_cuenta) + \
        salida_tardia_tercera_cuenta.cta_salida.saldo(movimiento=salida_tardia_tercera_cuenta)


def test_si_recibe_dia_devuelve_suma_de_saldos_diarios_de_cuentas(
        cuenta, cuenta_2, entrada, salida, salida_posterior, entrada_posterior_otra_cuenta, salida_tardia_tercera_cuenta):
    dia = salida_posterior.dia
    assert saldo_general_historico(dia=dia) == cuenta.saldo(dia=dia) + cuenta_2.saldo(dia=dia)


def test_si_no_recibe_dia_ni_movimiento_devuelve_saldo_al_ultimo_dia(
        cuenta, cuenta_2, entrada, salida,
        salida_posterior, entrada_posterior_otra_cuenta,
        salida_tardia_tercera_cuenta, dia_tardio):
    assert saldo_general_historico() == saldo_general_historico(dia=dia_tardio)


def test_si_no_recibe_movimiento_y_no_encuentra_dias_devuelve_cero(cuenta, cuenta_2):
    assert saldo_general_historico(cuentas=[cuenta, cuenta_2]) == 0


def test_si_no_hay_cuentas_independientes_en_la_base_de_datos_devuelve_cero(dia):
    assert saldo_general_historico(dia=dia) == 0


def test_suma_una_sola_vez_saldo_de_cuentas_acumulativas(
        cuenta, entrada_posterior_otra_cuenta, salida_tardia_tercera_cuenta, fecha_tardia_plus):
    cuenta = dividir_en_dos_subcuentas(
        cuenta, saldo=3, fecha= fecha_tardia_plus)
    mov = Movimiento.crear(
        'Ultimo mov',
        importe=5,
        cta_entrada=salida_tardia_tercera_cuenta.cta_salida,
        fecha=fecha_tardia_plus+timedelta(1)
    )
    assert saldo_general_historico(mov) == sum([
        c.saldo(movimiento=mov) for c in (
            cuenta,
            entrada_posterior_otra_cuenta.cta_entrada,
            salida_tardia_tercera_cuenta.cta_salida,
        )
    ])


@pytest.mark.parametrize("compra", [True, False])
def test_devuelve_importe_en_moneda_dada(
        cuenta, entrada, dolar, compra):
    assert \
        saldo_general_historico(entrada, moneda=dolar, compra=compra) == \
        round(saldo_general_historico(entrada) / dolar.cotizacion_al(entrada.dia.fecha, compra=compra), 2)


def test_incluye_cuentas_acumulativas_en_calculo_de_saldo(cuenta, entrada, salida, cuenta_acumulativa):
    assert saldo_general_historico() == cuenta.saldo() + cuenta_acumulativa.saldo()


# TODO: retirar (redundante)
def test_incluye_cuentas_acumulativas_anidadas_en_calculo_de_saldo(
        cuenta, entrada, salida, cuenta_acumulativa, subsubcuenta):
    assert saldo_general_historico() == cuenta.saldo() + cuenta_acumulativa.saldo()


def test_usa_batch_de_saldos_con_dia(cuenta, cuenta_2, dia, entrada, entrada_otra_cuenta):
    with CaptureQueriesContext(connection) as ctx:
        saldo_general_historico(dia=dia, cuentas=[cuenta, cuenta_2])

        queries_sd = sum(
            1 for q in ctx.captured_queries if "diario_saldodiario" in q["sql"]
        )
        assert queries_sd <= 2
