def test_devuelve_importe_del_movimiento(entrada):
    assert entrada.importe == entrada._importe


def test_asigna_valor_a_campo__importe(entrada):
    entrada.importe = 300
    assert entrada._importe == 300


def test_redondea_importe_al_asignar(entrada):
    entrada.importe = 300.462
    assert entrada._importe == 300.46
    entrada.importe = 300.468
    assert entrada._importe == 300.47
