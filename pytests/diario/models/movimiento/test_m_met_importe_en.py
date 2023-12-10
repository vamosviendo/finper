import pytest


@pytest.mark.parametrize('mov', ['entrada', 'salida', 'traspaso', 'entrada_en_euros'])
def test_devuelve_importe_del_movimiento_en_moneda_dada_redondeado_en_2_decimales(mov, dolar, request):
    mov = request.getfixturevalue(mov)
    assert \
        mov.importe_en(dolar) == \
        round(mov.importe * mov.moneda.cotizacion_en(dolar), 2)
