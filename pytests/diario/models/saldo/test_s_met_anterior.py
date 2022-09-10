def test_devuelve_ultimo_saldo_anterior_de_la_cuenta_por_fecha(saldo, saldo_anterior):
    assert saldo.anterior() == saldo_anterior


def test_dentro_de_fecha_devuelve_ultimo_saldo_anterior_de_la_cuenta_por_orden_dia(
        saldo, saldo_salida):
    assert saldo_salida.anterior() == saldo

    saldo.movimiento.orden_dia = 1
    saldo_salida.movimiento.orden_dia = 0
    saldo.movimiento.save()
    saldo_salida.movimiento.save()

    assert saldo.anterior() == saldo_salida


def test_si_no_hay_saldos_anteriores_por_fecha_u_orden_dia_devuelve_None(saldo):
    assert saldo.anterior() is None
