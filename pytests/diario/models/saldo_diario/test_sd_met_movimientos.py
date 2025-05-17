def test_devuelve_todos_los_movimientos_del_dia_de_la_cuenta_del_saldo_diario(
        saldo_diario, entrada, salida):
    assert list(saldo_diario.movimientos()) == [entrada, salida]

def test_no_incluye_movimientos_del_dia_de_otra_cuenta(saldo_diario, entrada, salida, entrada_otra_cuenta):
    assert entrada_otra_cuenta not in saldo_diario.movimientos()

def test_no_incluye_movimientos_de_la_cuenta_de_otro_dia(saldo_diario, entrada, salida, salida_posterior):
    assert salida_posterior not in saldo_diario.movimientos()
