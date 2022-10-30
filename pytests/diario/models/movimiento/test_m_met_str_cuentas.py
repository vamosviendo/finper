def test_devuelve_str_con_cuentas_de_entrada_y_salida(traspaso):
    assert \
        traspaso.str_cuentas() == \
        f"+{traspaso.cta_entrada.slug} -{traspaso.cta_salida.slug}"


def test_en_movimiento_de_entrada_devuelve_cuenta_de_entrada(entrada):
    assert entrada.str_cuentas() == f"+{entrada.cta_entrada.slug}"


def test_en_movimiento_de_salida_devuelve_cuenta_de_salida(salida):
    assert salida.str_cuentas() == f"-{salida.cta_salida.slug}"
