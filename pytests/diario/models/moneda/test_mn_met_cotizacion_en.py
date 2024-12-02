import pytest


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_devuelve_cotizacion_de_una_moneda_en_otra_moneda_dada(sentido, dolar, euro):
    met_cotizacion_dolar = getattr(dolar, f"cotizacion_{sentido}_en")
    cotizacion_dolar_en = met_cotizacion_dolar(euro)

    met_cotizacion_euro = getattr(euro, f"cotizacion_{sentido}_en")
    cotizacion_euro_en = met_cotizacion_euro(dolar)

    assert cotizacion_dolar_en == getattr(dolar, f"cotizacion_{sentido}") / getattr(euro, f"cotizacion_{sentido}")
    assert cotizacion_euro_en == getattr(euro, f"cotizacion_{sentido}") / getattr(dolar, f"cotizacion_{sentido}")
