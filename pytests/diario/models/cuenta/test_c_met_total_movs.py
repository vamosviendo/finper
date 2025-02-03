import pytest

from diario.models import Movimiento
from utils.varios import el_que_no_es

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
def test_computa_correctamente_movimientos_en_moneda_distinta_a_la_de_la_cuenta(
        tipo, cuenta, cuenta_en_dolares, dolar, peso, fecha):
    compra = tipo == "compra"
    tipo_opuesto = el_que_no_es(tipo, "compra", "venta")
    sentido = "entrada" if tipo == "venta" else "salida"
    sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")

    Movimiento.crear(**{
        "concepto": f"{tipo_opuesto} de dólares expresada en pesos",
        "fecha": fecha,
        f"cta_{sentido}": cuenta_en_dolares,
        f"cta_{sentido_opuesto}": cuenta,
        "importe": 850,
        "moneda": peso,
        "cotizacion": 1.0 / dolar.cotizacion_al(fecha, compra=compra)
    })

    assert abs(cuenta_en_dolares.total_movs()) == round(850 * peso.cotizacion_en(dolar, compra=compra), 2)
