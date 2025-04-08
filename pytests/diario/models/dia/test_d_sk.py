def test_devuelve_sk_basada_en_fecha_del_dia(dia):
    assert dia.sk == dia.fecha.strftime("%Y%m%d")
