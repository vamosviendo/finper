def test_devuelven_titulares_de_cuenta_de_salida_y_entrada_del_movimiento_respectivamente(
        credito, titular, otro_titular):
    assert credito.emisor == otro_titular
    assert credito.receptor == titular


def test_devuelven_None_si_no_hay_cuenta_de_entrada_o_salida(entrada, salida):
    assert entrada.emisor is None
    assert salida.receptor is None
