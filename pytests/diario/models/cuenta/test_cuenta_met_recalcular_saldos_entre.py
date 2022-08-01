import pytest
from datetime import timedelta

from diario.models import Movimiento
from utils.tiempo import Posicion

pytestmark = pytest.mark.django_db


def test_recalcula_saldos_de_cuenta_a_partir_de_fecha_desde(cuenta, saldo, saldo_posterior):
    importe_saldo = saldo.importe
    saldo.importe = 100
    saldo.save()
    importe_saldo_posterior = saldo_posterior.importe
    saldo_posterior.importe = 1000
    saldo_posterior.save()

    cuenta.recalcular_saldos_entre((Posicion(saldo.posicion.fecha-timedelta(1))))
    saldo.refresh_from_db(fields=['_importe'])
    saldo_posterior.refresh_from_db(fields=['_importe'])

    assert saldo.importe == importe_saldo
    assert saldo_posterior.importe == importe_saldo_posterior


def test_no_recalcula_saldos_anteriores_a_fecha(cuenta, saldo_anterior):
    saldo_anterior.importe = 100
    saldo_anterior.save()
    cuenta.recalcular_saldos_entre(Posicion(saldo_anterior.posicion.fecha+timedelta(1)))
    saldo_anterior.refresh_from_db(fields=['_importe'])

    assert saldo_anterior.importe == 100


def test_recalcula_saldos_de_cuenta_a_partir_de_orden_dia_inclusive(cuenta, saldo):
    segundo_saldo_del_dia = Movimiento.crear(
        'segundo mov del dia', 12, cuenta, fecha=saldo.posicion.fecha).saldo_ce()
    tercer_saldo_del_dia = Movimiento.crear(
        'tercer mov del dia', 15, None, cuenta, fecha=saldo.posicion.fecha).saldo_cs()

    importe_segundo_saldo = segundo_saldo_del_dia.importe
    segundo_saldo_del_dia.importe = 100
    segundo_saldo_del_dia.save()
    importe_tercer_saldo = tercer_saldo_del_dia.importe
    tercer_saldo_del_dia.importe = 200
    tercer_saldo_del_dia.save()

    cuenta.recalcular_saldos_entre(Posicion(saldo.posicion.fecha, orden_dia=1))
    segundo_saldo_del_dia.refresh_from_db(fields=['_importe'])
    tercer_saldo_del_dia.refresh_from_db(fields=['_importe'])

    assert segundo_saldo_del_dia.importe == importe_segundo_saldo
    assert tercer_saldo_del_dia.importe == importe_tercer_saldo


def test_no_recalcula_saldos_de_cuenta_en_la_misma_fecha_anteriores_a_orden_dia(
        saldo, saldo_traspaso_cuenta, saldo_salida):
    assert saldo.posicion.orden_dia == 0
    saldo.importe = 200
    saldo.save()

    saldo.cuenta.recalcular_saldos_entre(
        Posicion(saldo.posicion.fecha, orden_dia=1)
    )
    saldo.refresh_from_db(fields=['_importe'])

    assert saldo.importe == 200


def test_no_recalcula_saldos_posteriores_a_fecha_de_pos_hasta(cuenta, saldo, saldo_posterior, saldo_tardio):
    saldo_tardio.importe = 20000
    saldo_tardio.save()

    cuenta.recalcular_saldos_entre(
        Posicion(saldo.posicion.fecha),
        Posicion(saldo_tardio.posicion.fecha-timedelta(1))
    )
    saldo_tardio.refresh_from_db(fields=['_importe'])

    assert saldo_tardio.importe == 20000


def test_recalcula_saldos_de_fecha_de_pos_hasta(cuenta, saldo, saldo_posterior):
    importe_saldo_posterior = saldo_posterior.importe
    saldo_posterior.importe = 200
    saldo_posterior.save()

    cuenta.recalcular_saldos_entre(
        Posicion(saldo.posicion.fecha),
        Posicion(saldo_posterior.posicion.fecha)
    )
    saldo_posterior.refresh_from_db(fields=['_importe'])

    assert saldo_posterior.importe == importe_saldo_posterior


def test_no_recalcula_saldos_de_fecha_hasta_posteriores_a_orden_dia_de_pos_hasta(
        cuenta, fecha, saldo, saldo_salida, saldo_traspaso_cuenta):
    assert saldo_traspaso_cuenta.posicion.orden_dia == 2
    saldo_traspaso_cuenta.importe = 200
    saldo_traspaso_cuenta.save()

    cuenta.recalcular_saldos_entre(
        Posicion(fecha),
        Posicion(fecha, orden_dia=1)
    )
    saldo_traspaso_cuenta.refresh_from_db(fields=['_importe'])

    assert saldo_traspaso_cuenta.importe == 200


def test_recalcula_saldos_de_fecha_hasta_con_orden_dia_igual_a_orden_dia_de_pos_hasta(
        cuenta, fecha_anterior, fecha, saldo_anterior, saldo, saldo_salida):
    assert saldo_salida.posicion.orden_dia == 1
    importe_saldo_salida = saldo_salida.importe
    saldo_salida.importe = 200
    saldo_salida.save()

    cuenta.recalcular_saldos_entre(
        Posicion(fecha_anterior),
        Posicion(fecha, orden_dia=1)
    )
    saldo_salida.refresh_from_db(fields=['_importe'])

    assert saldo_salida.importe == importe_saldo_salida


def test_si_no_hay_saldos_anteriores_actualiza_del_primer_saldo_en_adelante(
        cuenta, fecha, saldo, saldo_posterior):
    importe_saldo = saldo.importe
    importe_saldo_posterior = saldo_posterior.importe
    saldo.importe = 200
    saldo.save()
    saldo_posterior.importe = 400
    saldo_posterior.save()

    cuenta.recalcular_saldos_entre(Posicion(fecha-timedelta(1)))
    saldo.refresh_from_db(fields=['_importe'])
    saldo_posterior.refresh_from_db(fields=['_importe'])

    assert saldo.importe == importe_saldo
    assert saldo_posterior.importe == importe_saldo_posterior
