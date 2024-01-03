from diario.utils.utils_saldo import saldo_general_historico


def test_devuelve_saldo_del_ultimo_movimiento_del_dia(dia, entrada, salida):
    assert dia.saldo() == saldo_general_historico(salida)


def test_si_dia_no_tiene_movimientos_devuelve_saldo_del_dia_anterior(dia, dia_anterior, entrada_anterior):
    assert dia_anterior.saldo() == saldo_general_historico(entrada_anterior)
    assert dia.saldo() == dia_anterior.saldo()


def test_si_no_hay_dia_anterior_devuelve_0(dia):
    assert dia.saldo() == 0


def test_si_ningun_dia_anterior_tiene_movimientos_devuelve_0(dia, dia_anterior, dia_temprano):
    assert dia.saldo() == 0
