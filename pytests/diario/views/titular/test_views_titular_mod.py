from django.urls import reverse
from pytest_django import asserts


def test_usa_template_cta_form(client, titular):
    response = client.get(reverse('tit_mod', args=[titular.titname]))
    asserts.assertTemplateUsed(response, 'diario/tit_form.html')


def test_muestra_campo_nombre(client, titular):
    response = client.get(reverse('tit_mod', args=[titular.titname]))
    assert 'nombre' in response.context['form'].fields.keys()


def test_muestra_campo_titname(client, titular):
    response = client.get(reverse('tit_mod', args=[titular.titname]))
    assert 'titname' in response.context['form'].fields.keys()


def test_muestra_campo_fecha_alta(client, titular):
    response = client.get(reverse('tit_mod', args=[titular.titname]))
    assert 'fecha_alta' in response.context['form'].fields.keys()


def test_post_redirige_a_home(client, titular, fecha):
    response = client.post(
        reverse('tit_mod', args=[titular.titname]),
        data={'titname': 'nuevo', 'fecha_alta': fecha}
    )
    asserts.assertRedirects(response, reverse('home'))
