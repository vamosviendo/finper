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


def test_computa_correctamente_movimientos_en_moneda_distinta_a_la_de_la_cuenta(
        cuenta, cuenta_en_dolares, dolar, peso, fecha):
    Movimiento.crear(
        "Compra de dólares expresada en pesos",
        fecha=fecha,
        cta_entrada=cuenta_en_dolares,
        cta_salida=cuenta,
        importe=850, moneda=peso,
        cotizacion=1.0 / dolar.cotizacion_al(fecha)
    )
    assert cuenta_en_dolares.total_movs() == round(850 * peso.cotizacion_en(dolar), 2)
