import pytest


@pytest.mark.parametrize('mov', ['entrada', 'salida', 'traspaso', 'entrada_en_euros'])
@pytest.mark.parametrize('compra', [True, False])
def test_devuelve_importe_cotizado_para_la_compra_o_para_la_venta_segun_argumento_compra(mov, compra, dolar, request):
    mov = request.getfixturevalue(mov)
    assert \
        mov.importe_en(dolar, compra=compra) == \
        round(mov.importe * mov.moneda.cotizacion_en(dolar, compra=compra), 2)


@pytest.mark.parametrize('mov', ['entrada', 'salida', 'traspaso', 'entrada_en_euros'])
def test_devuelve_importe_del_movimiento_en_moneda_dada_redondeado_en_2_decimales(mov, dolar, request):
    mov = request.getfixturevalue(mov)
    assert \
        mov.importe_en(dolar) == \
        round(mov.importe * mov.moneda.cotizacion_en(dolar, compra=False), 2)
