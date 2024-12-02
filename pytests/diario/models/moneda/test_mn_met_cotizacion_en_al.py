import pytest

@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_devuelve_cotizacion_de_una_moneda_en_otra_moneda_dada_a_la_fecha_dada(
        sentido, dolar, euro,
        cotizacion_posterior, cotizacion_tardia,
        cotizacion_posterior_euro, cotizacion_tardia_euro, fecha_posterior):
    cotizacion_dolar_en_al = getattr(dolar, f"cotizacion_{sentido}_en_al")(euro, fecha_posterior)
    cotizacion_euro_en_al = getattr(euro, f"cotizacion_{sentido}_en_al")(dolar, fecha_posterior)

    cotizacion_dolar_al = getattr(dolar, f"cotizacion_{sentido}_al")
    cotizacion_euro_al = getattr(euro, f"cotizacion_{sentido}_al")
    assert cotizacion_dolar_en_al == cotizacion_dolar_al(fecha_posterior) / cotizacion_euro_al(fecha_posterior)
    assert cotizacion_euro_en_al == cotizacion_euro_al(fecha_posterior) / cotizacion_dolar_al(fecha_posterior)