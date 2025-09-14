from pytest_django import asserts


def test_usa_template_moneda(client, dolar):
    response = client.get(dolar.get_absolute_url())
    asserts.assertTemplateUsed(response, "diario/moneda.html")


def test_pasa_moneda_a_tempate(client, dolar):
    response = client.get(dolar.get_absolute_url())
    assert response.context.get("moneda") == dolar


def test_pasa_cotizaciones_de_moneda_a_template_ordenadas_por_fecha_a_la_inversa(client, dolar, cotizacion_dolar, cotizacion_posterior_dolar, cotizacion_tardia_dolar):
    response = client.get(dolar.get_absolute_url())
    assert list(response.context.get("cotizaciones")) == list(dolar.cotizaciones.all().order_by("fecha").reverse())


def test_pasa_solo_las_ultimas_20_cotizaciones(client, dolar, mas_de_20_cotizaciones_dolar):
    response = client.get(dolar.get_absolute_url())
    assert len(list(response.context.get("cotizaciones"))) == 20


def test_puede_pasar_cotizaciones_anteriores(client, dolar, mas_de_20_cotizaciones_dolar):
    response = client.get(dolar.get_absolute_url() + "?page=2", follow=True)
    cotizaciones = response.context.get("cotizaciones")
    assert mas_de_20_cotizaciones_dolar.last() not in cotizaciones
    assert mas_de_20_cotizaciones_dolar.first() in cotizaciones
