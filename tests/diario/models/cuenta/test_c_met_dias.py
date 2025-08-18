def test_devuelve_todos_los_dias_en_los_que_una_cuenta_tiene_movimientos(
        cuenta, dia, dia_posterior, dia_tardio, entrada, entrada_tardia):
    dias = cuenta.dias()
    for d in [dia, dia_tardio]:
        assert d in dias
    assert dia_posterior not in dias
