import pytest

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures(
    'entrada',
    'traspaso_posterior',
    'entrada_tardia',
    'entrada_posterior_otra_cuenta')
def test_devuelve_cantidad_de_entradas_mas_cantidad_de_salidas(cuenta):
    assert cuenta.cantidad_movs() == 3
