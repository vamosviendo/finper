def test_devuelve_identidad_basada_en_fecha_del_dia(dia):
    assert dia.identidad == dia.fecha.strftime("%Y%m%d")