import pytest


@pytest.mark.parametrize(
    'mov', [
        'entrada_en_dolares',
        'entrada_en_euros',
        'mov_distintas_monedas_en_moneda_cta_entrada',
        'mov_distintas_monedas_en_moneda_cta_salida'
    ])
def test_devuelve_contenido_del_campo__cotizacion(mov, request):
    movimiento = request.getfixturevalue(mov)
    assert movimiento.cotizacion == movimiento._cotizacion


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_fija_contenido_del_campo__cotizacion(sentido, request):
    movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    movimiento.cotizacion = 184
    assert movimiento._cotizacion == 184
