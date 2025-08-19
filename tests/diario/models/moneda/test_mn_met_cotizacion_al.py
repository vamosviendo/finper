import pytest

from diario.models import Cotizacion


@pytest.mark.parametrize("sentido, compra", [("compra", True), ("venta", False)])
def test_devuelve_valor_de_cotizacion_vigente_a_la_fecha_dada(
        sentido, compra, cotizacion_dolar, cotizacion_posterior_dolar, dolar, fecha):
    cot_actual = Cotizacion.tomar(moneda=dolar, fecha=fecha)
    assert dolar.cotizacion_al(fecha, compra=compra) == getattr(cot_actual, f"importe_{sentido}")


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_cotizacion_compra_venta_devuelve_valor_de_cotizacion_vigente_a_la_fecha_dada(
        sentido, cotizacion_dolar, cotizacion_posterior_dolar, dolar, fecha):
    met_cotizacion = getattr(dolar, f"cotizacion_{sentido}_al")
    cotizacion_al = met_cotizacion(fecha)

    cot_actual = Cotizacion.tomar(moneda=dolar, fecha=fecha)
    importe = getattr(cot_actual, f"importe_{sentido}")

    assert cotizacion_al == importe
