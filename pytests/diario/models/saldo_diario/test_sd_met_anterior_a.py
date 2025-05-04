def test_devuelve_ultimo_saldo_diario_anterior_de_la_cuenta_y_el_dia_dados(saldo_diario_anterior, saldo_diario):
    assert saldo_diario.anterior_a(cuenta=saldo_diario.cuenta, dia=saldo_diario.dia) == saldo_diario_anterior


def test_si_no_hay_saldos_diarios_anteriores_devuelve_None(saldo_diario):
    assert saldo_diario.anterior_a(cuenta=saldo_diario.cuenta, dia=saldo_diario.dia) == None
