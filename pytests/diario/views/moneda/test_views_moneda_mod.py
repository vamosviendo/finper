from django.urls import reverse
from pytest_django import asserts


def test_usa_template_moneda_form(client, dolar):
    response = client.get(reverse('mon_mod', args=[dolar.monname]))
    asserts.assertTemplateUsed(response, 'diario/moneda_form.html')


def test_post_redirige_a_home(client, dolar):
    response = client.post(
        reverse('mon_mod', args=[dolar.monname]),
        data={'monname': 'nuevo', 'nombre': 'nombre nuevo', 'cotizacion': 2}
    )
    print(response.content.decode())
    asserts.assertRedirects(response, reverse('home'))
