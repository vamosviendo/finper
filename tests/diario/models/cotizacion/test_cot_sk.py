def test_devuelve_sk_basada_en_fecha_y_sk_de_moneda(cotizacion):
    assert \
        cotizacion.sk == \
        f"{cotizacion.fecha.year}{cotizacion.fecha.month}{cotizacion.fecha.day}{cotizacion.moneda.sk}"
