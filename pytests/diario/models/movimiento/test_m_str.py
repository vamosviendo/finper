def test_muestra_movimiento_con_cuenta_de_entrada_y_salida(traspaso):
    assert \
        traspaso.__str__() == \
        f"{traspaso.fecha} {traspaso.concepto}: {traspaso.importe:.2f} " \
        f"+{traspaso.cta_entrada} -{traspaso.cta_salida}"


def test_muestra_movimiento_sin_cuenta_de_salida(entrada):
    assert \
        entrada.__str__() == \
        f"{entrada.fecha} {entrada.concepto}: {entrada.importe:.2f} " \
        f"+{entrada.cta_entrada}"


def test_muestra_movimiento_sin_cuenta_de_entrada(salida):
    assert \
        salida.__str__() == \
        f"{salida.fecha} {salida.concepto}: {salida.importe:.2f} " \
        f"-{salida.cta_salida}"
