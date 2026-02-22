import pytest


def test_muestra_movimiento_con_cuenta_de_entrada_y_salida(traspaso):
    assert traspaso.__str__() == f"{traspaso.fecha} {traspaso.orden_dia} {traspaso.concepto} - " \
                                 f"{traspaso.cta_salida} -> {traspaso.cta_entrada}: " \
                                 f"{traspaso.importe:.2f} {traspaso.moneda.plural}"


def test_muestra_movimiento_sin_cuenta_de_salida_o_salida(entrada, salida):
    assert entrada.__str__() == f"{entrada.fecha} {entrada.orden_dia} {entrada.concepto} - ... -> " \
                                f"{entrada.cta_entrada}: {entrada.importe:.2f} {entrada.moneda.plural}"
    assert salida.__str__() == f"{salida.fecha} {salida.orden_dia} {salida.concepto} - {salida.cta_salida} " \
                               f"-> ...: {salida.importe:.2f} {salida.moneda.plural}"


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_muestra_movimiento_entre_cuentas_en_distinta_moneda(sentido, request,
        # mov_distintas_monedas_en_moneda_cta_entrada,
        # mov_distintas_monedas_en_moneda_cta_salida,
):
    # mov = mov_distintas_monedas_en_moneda_cta_entrada
    mov = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    assert \
        mov.__str__() == \
        f"{mov.fecha} {mov.orden_dia} {mov.concepto} - " \
        f"{mov.cta_salida} -> {mov.cta_entrada}: " \
        f"{mov.importe_cta_salida:.2f} {mov.cta_salida.moneda.plural} -> " \
        f"{mov.importe_cta_entrada:.2f} {mov.cta_entrada.moneda.plural}"
    # assert False, "Escribir para moneda en moneda cta salida"
