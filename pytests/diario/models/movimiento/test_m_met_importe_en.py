import pytest


@pytest.mark.parametrize('mov', ['entrada', 'salida', 'traspaso', 'entrada_en_euros'])
def test_devuelve_importe_del_movimiento_en_moneda_dada(mov, dolar, request):
    mov = request.getfixturevalue(mov)
    assert \
        mov.importe_en(dolar) == \
        mov.importe * mov.moneda.cotizacion_en(dolar)
