def test_devuelve_cotizacion_de_una_moneda_en_otra_moneda_dada_a_la_fecha_dada(
        dolar, euro,
        cotizacion_posterior, cotizacion_tardia,
        cotizacion_posterior_euro, cotizacion_tardia_euro, fecha_posterior):
    assert \
        dolar.cotizacion_en_al(euro, fecha_posterior) == \
        dolar.cotizacion_al(fecha_posterior) / euro.cotizacion_al(fecha_posterior)
    assert \
        euro.cotizacion_en_al(dolar, fecha_posterior) == \
        euro.cotizacion_al(fecha_posterior) / dolar.cotizacion_al(fecha_posterior)