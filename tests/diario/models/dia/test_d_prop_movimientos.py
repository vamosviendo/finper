def test_devuelve_movimientos_del_dia(dia, entrada, salida, salida_posterior):
    movs = dia.movimientos
    assert entrada in movs
    assert salida in movs
    assert salida_posterior not in movs
