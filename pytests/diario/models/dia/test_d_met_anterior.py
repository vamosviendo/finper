def test_devuelve_dia_anterior_a_self(dia, dia_anterior, dia_temprano):
    assert dia.anterior() == dia_anterior
