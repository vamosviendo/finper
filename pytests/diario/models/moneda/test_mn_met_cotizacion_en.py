def test_devuelve_cotizacion_de_una_moneda_en_otra_moneda_dada(dolar, euro):
    assert dolar.cotizacion_en(euro) == dolar.cotizacion / euro.cotizacion
    assert euro.cotizacion_en(dolar) == euro.cotizacion / dolar.cotizacion
