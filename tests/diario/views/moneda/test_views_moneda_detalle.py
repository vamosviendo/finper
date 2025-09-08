from pytest_django import asserts


def test_usa_template_moneda(client, dolar):
    response = client.get(dolar.get_absolute_url())
    asserts.assertTemplateUsed(response, "diario/moneda.html")


def test_pasa_moneda_a_tempate(client, dolar):
    response = client.get(dolar.get_absolute_url())
    assert response.context.get("moneda") == dolar
