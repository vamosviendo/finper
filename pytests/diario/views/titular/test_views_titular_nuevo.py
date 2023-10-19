from django.urls import reverse
from pytest_django import asserts

from diario.forms import FormTitular


def test_get_usa_template_tit_form(client):
    response = client.get(reverse('tit_nuevo'))
    asserts.assertTemplateUsed(response, 'diario/tit_form.html')


def test_usa_form_FormTitular(client):
    response = client.get(reverse('tit_nuevo'))
    assert isinstance(response.context['form'], FormTitular)


def test_post_redirige_a_home(client, fecha):
    response = client.post(
        reverse('tit_nuevo'),
        data={'titname': 'tito', 'nombre': 'Tito Gómez', 'fecha_alta': fecha})
    asserts.assertRedirects(response, reverse('home'))
