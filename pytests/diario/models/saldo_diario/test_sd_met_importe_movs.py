def test_devuelve_importe_total_de_los_movimientos_de_la_cuenta_en_el_dia(
        saldo_diario, entrada, salida, traspaso):
    assert \
        saldo_diario.importe_movs() == \
        entrada.importe_cta_entrada + salida.importe_cta_salida + traspaso.importe_cta_entrada


def test_no_toma_importe_de_movimientos_que_no_son_de_la_cuenta_en_el_dia(
        saldo_diario, entrada, salida, entrada_otra_cuenta):
    assert saldo_diario.importe_movs() == entrada.importe_cta_entrada + salida.importe_cta_salida


def test_no_toma_importe_de_movimientos_de_la_cuenta_en_otro_dia(saldo_diario, entrada, salida, salida_posterior):
    assert saldo_diario.importe_movs() == entrada.importe_cta_entrada + salida.importe_cta_salida
