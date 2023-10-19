from django.urls import reverse
from pytest_django import asserts

from diario.forms import FormTitular


def test_usa_template_cta_form(client, titular):
    response = client.get(reverse('tit_mod', args=[titular.titname]))
    asserts.assertTemplateUsed(response, 'diario/tit_form.html')


def test_usa_form_FormTitular(client, titular):
    response = client.get(reverse('tit_mod', args=[titular.titname]))
    assert isinstance(response.context['form'], FormTitular)


def test_post_redirige_a_home(client, titular, fecha):
    response = client.post(
        reverse('tit_mod', args=[titular.titname]),
        data={'titname': 'nuevo', 'fecha_alta': fecha}
    )
    asserts.assertRedirects(response, reverse('home'))
