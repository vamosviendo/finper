def test_devuelve_sk_basada_en_fecha_y_sk_de_moneda(cotizacion_dolar):
    assert \
        cotizacion_dolar.sk == \
        f"{cotizacion_dolar.fecha.year}{cotizacion_dolar.fecha.month}" \
        f"{cotizacion_dolar.fecha.day}{cotizacion_dolar.moneda.sk}"
