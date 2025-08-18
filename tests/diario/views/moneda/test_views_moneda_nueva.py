from django.urls import reverse
from pytest_django import asserts

from diario.forms import FormMoneda


def test_get_usa_template_mon_form(client):
    response = client.get(reverse('mon_nueva'))
    asserts.assertTemplateUsed(response, 'diario/moneda_form.html')


def test_usa_form_formmoneda(client):
    response = client.get(reverse(('mon_nueva')))
    assert 'form' in response.context.keys()
    assert isinstance(response.context['form'], FormMoneda)


def test_post_redirige_a_home(client):
    response = client.post(
        reverse('mon_nueva'),
        data={'sk': 'd', 'nombre': 'Dólar', 'cotizacion': '15'}
    )
    asserts.assertRedirects(response, reverse('home'))
