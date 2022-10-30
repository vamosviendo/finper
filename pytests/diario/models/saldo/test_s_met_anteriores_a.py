from datetime import timedelta

from diario.models import Saldo
from utils.tiempo import Posicion


def test_incluye_saldos_de_cuenta_anteriores_a_fecha_dada(
        saldo, saldo_anterior, saldo_temprano, cuenta):
    fecha = saldo.posicion.fecha - timedelta(1)
    anteriores = Saldo.anteriores_a(cuenta, Posicion(fecha))
    assert saldo_anterior in anteriores
    assert saldo_temprano in anteriores


def test_incluye_saldos_de_cuenta_de_la_misma_fecha_y_orden_dia_anterior(
        saldo, saldo_salida, cuenta):
    assert saldo in Saldo.anteriores_a(
        cuenta,
        Posicion(saldo.posicion.fecha, orden_dia=1)
    )


def test_no_incluye_saldos_de_cuenta_de_fecha_posterior_a_la_dada(
        saldo, cuenta):
    assert saldo not in Saldo.anteriores_a(
        cuenta,
        Posicion(saldo.posicion.fecha - timedelta(1))
    )


def test_no_incluye_saldos_de_cuenta_de_la_misma_fecha_y_orden_dia_anterior(
        saldo, saldo_salida, cuenta):
    assert saldo_salida not in Saldo.anteriores_a(
        cuenta,
        Posicion(saldo.posicion.fecha, orden_dia=0)
    )


def test_con_inclusive_od_false_no_incluye_saldo_con_la_fecha_y_orden_dia_dados(
        saldo, cuenta):
    assert saldo not in Saldo.anteriores_a(
        cuenta,
        Posicion(saldo.posicion.fecha, orden_dia=0),
        inclusive_od=False
    )


def test_con_inclusive_od_true_incluye_saldo_con_la_fecha_y_orden_dia_dados(
        saldo, cuenta):
    assert saldo in Saldo.anteriores_a(
        cuenta,
        Posicion(saldo.posicion.fecha, orden_dia=0),
        inclusive_od=True
    )
