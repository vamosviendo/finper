import pytest

from utils.varios import el_que_no_es


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_moneda_de_cuenta_es_igual_a_la_del_movimiento_devuelve_importe_del_movimiento(sentido, request):
    movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    assert abs(getattr(movimiento, f"importe_cta_{sentido}")) == abs(movimiento.importe)


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_moneda_de_cuenta_es_distinta_de_la_del_movimiento_devuelve_importe_del_movimiento_cotizado(
        sentido, request):
    movimiento = request.getfixturevalue(f"mov_distintas_monedas_en_moneda_cta_{sentido}")
    sentido_opuesto = el_que_no_es(sentido, "entrada", "salida")

    assert \
        abs(getattr(movimiento, f"importe_cta_{sentido_opuesto}")) == \
        round(movimiento.importe * movimiento.cotizacion, 2)


def test_si_no_hay_cuenta_de_entrada_importe_cta_entrada_devuelve_None(salida):
    assert salida.importe_cta_entrada is None


def test_si_no_hay_cuenta_de_salida_importe_cta_salida_devuelve_none(entrada_en_dolares):
    assert entrada_en_dolares.importe_cta_salida is None


def test_importe_cta_salida_devuelve_importe_en_negativo(salida):
    assert salida.importe_cta_salida == -salida.importe
