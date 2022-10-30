import pytest

from diario.models import Movimiento

pytestmark = pytest.mark.usefixtures(
        'entrada',
        'traspaso_posterior',
        'entrada_tardia',
        'entrada_posterior_otra_cuenta'
    )


def test_devuelve_suma_de_importes_de_entradas_menos_suma_de_importes_de_salidas(cuenta):
    assert cuenta.total_movs() == 110


def test_funciona_correctamente_con_decimales(cuenta):
    Movimiento.crear(
        'Movimiento con decimales', cta_salida=cuenta, importe=50.32)
    assert cuenta.total_movs() == round(110 - 50.32, 2)
