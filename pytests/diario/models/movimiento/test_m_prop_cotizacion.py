import pytest


@pytest.mark.parametrize('mov', ['entrada_en_dolares', 'entrada_en_euros', 'mov_distintas_monedas'])
def test_devuelve_contenido_del_campo__cotizacion(mov, request):
    movimiento = request.getfixturevalue(mov)
    assert movimiento.cotizacion == movimiento._cotizacion


def test_fija_contenido_del_campo__cotizacion(mov_distintas_monedas):
    mov_distintas_monedas.cotizacion = 184
    assert mov_distintas_monedas._cotizacion == 184
