from django.urls import reverse
from pytest_django import asserts


def test_get_usa_template_mon_form(client):
    response = client.get(reverse('mon_nueva'))
    asserts.assertTemplateUsed(response, 'diario/moneda_form.html')


def test_post_redirige_a_home(client):
    response = client.post(
        reverse('mon_nueva'),
        data={'monname': 'd', 'nombre': 'Dólar', 'cotizacion': '15'}
    )
    asserts.assertRedirects(response, reverse('home'))
