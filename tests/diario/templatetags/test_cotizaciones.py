import pytest

from diario.templatetags.cotizaciones import cotizacion
from utils.numeros import float_format


@pytest.mark.parametrize("compra", (True, False))
def test_devuelve_la_ultima_cotizacion_de_una_moneda_dada(dolar, cotizacion_dolar, cotizacion_posterior_dolar, compra):
    attr_importe = "importe_compra" if compra else "importe_venta"
    context = dict()
    assert \
        cotizacion(context, moneda=dolar, compra=compra) == \
        float_format(getattr(cotizacion_posterior_dolar, attr_importe))


@pytest.mark.parametrize("compra", (True, False))
def test_si_hay_movimiento_en_el_context_devuelve_cotizacion_a_la_fecha_del_movimiento(
        dolar, entrada_anterior, salida_posterior, cotizacion_dolar, cotizacion_posterior_dolar, compra):
    attr_importe = "importe_compra" if compra else "importe_venta"
    context = {"movimiento": entrada_anterior}
    assert cotizacion(context, moneda=dolar, compra=compra) == float_format(getattr(cotizacion_dolar, attr_importe))


@pytest.mark.parametrize("compra", (True, False))
def test_si_no_hay_cotizacion_el_dia_del_movimiento_en_el_context_devuelve_ultima_cotizacion_anterior(
        dolar, entrada, salida_posterior, cotizacion_dolar, cotizacion_posterior_dolar, compra):
    attr_importe = "importe_compra" if compra else "importe_venta"
    context = {"movimiento": entrada}
    assert cotizacion(context, moneda=dolar, compra=compra) == float_format(getattr(cotizacion_dolar, attr_importe))


@pytest.mark.parametrize("compra", (True, False))
def test_si_no_hay_cotizaciones_anteriores_al_dia_del_movimiento_devuelve_1():
    pass
