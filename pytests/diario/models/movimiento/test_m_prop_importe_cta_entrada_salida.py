def test_si_moneda_de_cuenta_es_igual_a_la_del_movimiento_devuelve_importe_del_movimiento(mov_distintas_monedas):
    assert mov_distintas_monedas.importe_cta_salida == mov_distintas_monedas.importe


def test_si_moneda_de_cuenta_es_distinta_de_la_del_movimiento_devuelve_importe_del_movimiento_cotizado(
        mov_distintas_monedas):
    assert \
        mov_distintas_monedas.importe_cta_entrada == \
        round(mov_distintas_monedas.importe / mov_distintas_monedas.cotizacion, 2)


def test_si_no_hay_cuenta_de_entrada_importe_cta_entrada_devuelve_None(salida):
    assert salida.importe_cta_entrada is None


def test_si_no_hay_cuenta_de_salida_importe_cta_salida_devuelve_none(entrada_en_dolares):
    assert entrada_en_dolares.importe_cta_salida is None
