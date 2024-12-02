import pytest

from diario.models import Cotizacion


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_devuelve_valor_de_cotizacion_vigente_a_la_fecha_dada(sentido, cotizacion, cotizacion_posterior, dolar, fecha):
    met_cotizacion = getattr(dolar, f"cotizacion_{sentido}_al")
    cotizacion_al = met_cotizacion(fecha)

    cot_actual = Cotizacion.tomar(moneda=dolar, fecha=fecha)
    importe = getattr(cot_actual, f"importe_{sentido}")

    assert cotizacion_al == importe
