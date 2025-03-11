from datetime import timedelta

import pytest

from diario.models import Movimiento
from utils.helpers_tests import signo


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_suma_importe_a_saldos_de_cta_entrada_posteriores_a_fecha_del_saldo(
        sentido, cuenta, saldo, saldo_posterior, saldo_tardio):
    importe_posterior = saldo_posterior.importe
    importe_tardio = saldo_tardio.importe

    s = signo(sentido == 'entrada')
    mov = Movimiento(
        concepto='movimiento',
        importe=100,
        fecha=saldo.posicion.fecha+timedelta(1)
    )
    setattr(mov, f'cta_{sentido}', cuenta)
    mov.clean_save()
    importe_mov = mov.importe
    saldo_posterior.refresh_from_db(fields=['_importe'])
    saldo_tardio.refresh_from_db(fields=['_importe'])

    assert saldo_posterior.importe == importe_posterior + s*importe_mov
    assert saldo_tardio.importe == importe_tardio + s*importe_mov


def test_no_suma_importe_a_saldos_posteriores_de_otras_cuentas(
        saldo, saldo_posterior_cuenta_2):
    importe_posterior_cuenta_2 = saldo_posterior_cuenta_2.importe
    Movimiento.crear(
        'mov', 200, saldo.cuenta, fecha=saldo.posicion.fecha+timedelta(1))
    saldo_posterior_cuenta_2.refresh_from_db(fields=['_importe'])

    assert saldo_posterior_cuenta_2.importe == importe_posterior_cuenta_2


def test_no_suma_importe_a_saldos_anteriores_de_la_cuenta(saldo):
    importe_saldo = saldo.importe
    Movimiento.crear(
        'mov posterior', 200, saldo.cuenta, fecha=saldo.posicion.fecha+timedelta(1))
    saldo.refresh_from_db(fields=['_importe'])

    assert saldo.importe == importe_saldo
