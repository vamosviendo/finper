from pytest_django import asserts


def test_post_redirige_a_pagina_de_moneda(client, dolar, cotizacion_dolar):
    response = client.post(cotizacion_dolar.get_delete_url())
    asserts.assertRedirects(response, dolar.get_absolute_url())
