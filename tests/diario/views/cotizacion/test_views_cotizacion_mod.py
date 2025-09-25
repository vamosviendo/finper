from pytest_django import asserts

from diario.forms import FormCotizacion


def test_usa_form_formcotizacion(client, cotizacion_dolar):
    response = client.get(cotizacion_dolar.get_edit_url())
    assert isinstance(response.context.get("form"), FormCotizacion)


def test_post_redirige_a_detalle_de_moneda_de_la_cotizacion(client, cotizacion_dolar):
    response = client.post(cotizacion_dolar.get_edit_url(), data={
        "fecha": cotizacion_dolar.fecha.isoformat(),
        "importe_compra": 405,
        "importe_venta": cotizacion_dolar.importe_venta or 0,
        "moneda": cotizacion_dolar.moneda
    })
    asserts.assertRedirects(response, cotizacion_dolar.moneda.get_absolute_url())
