import pytest


@pytest.mark.parametrize('mov', ['entrada_en_dolares', 'entrada_en_euros'])
def test_devuelve_cotizacion_de_la_moneda_de_la_cuenta(mov, request):
    movimiento = request.getfixturevalue(mov)
    assert movimiento.cotizacion == movimiento.moneda.cotizacion
