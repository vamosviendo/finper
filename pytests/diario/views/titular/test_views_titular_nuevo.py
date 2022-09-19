from django.urls import reverse
from pytest_django import asserts


def test_get_usa_template_tit_form(client):
    response = client.get(reverse('tit_nuevo'))
    asserts.assertTemplateUsed(response, 'diario/tit_form.html')


def test_post_redirige_a_home(client):
    response = client.post(
        reverse('tit_nuevo'),
        data={'titname': 'tito', 'nombre': 'Tito Gómez'})
    asserts.assertRedirects(response, reverse('home'))
