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


@pytest.mark.parametrize("tipo", ["compra", "venta"])
def test_computa_correctamente_movimientos_en_moneda_distinta_a_la_de_la_cuenta(cuenta_en_dolares, tipo, request):
    mov = request.getfixturevalue(f"{tipo}_dolares")
    compra = tipo == "venta"
    assert \
        abs(cuenta_en_dolares.total_movs()) == \
        round(mov.importe * mov.moneda.cotizacion_en(cuenta_en_dolares.moneda, compra=compra), 2)


def test_coincide_con_saldo_en_movimientos_en_distintas_monedas(
        cuenta, cuenta_en_dolares, entrada_en_dolares, venta_dolares):
    assert cuenta.total_movs() == cuenta.saldo()
    assert cuenta_en_dolares.total_movs() == cuenta_en_dolares.saldo()
