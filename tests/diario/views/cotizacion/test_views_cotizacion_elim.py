from django.urls import reverse
from pytest_django import asserts


def test_post_redirige_a_pagina_de_moneda(client, dolar, cotizacion_dolar):
    response = client.post(reverse("cot_elim", args=[dolar.pk]))
    asserts.assertRedirects(response, dolar.get_absolute_url())
