from django.urls import reverse
from pytest_django import asserts

from diario.models import Titular, Cuenta, CuentaInteractiva


def test_si_no_hay_titulares_redirige_a_crear_titular_con_get(client):
    Titular.todes().delete()
    response = client.get(reverse('cta_nueva'))
    asserts.assertRedirects(response, reverse('tit_nuevo'))


def test_usa_template_cta_form(client):
    response = client.get(reverse('cta_nueva'))
    asserts.assertTemplateUsed(response, 'diario/cta_form.html')


def test_post_guarda_cuenta_nueva(client):
    client.post(
        reverse('cta_nueva'),
        data={'nombre': 'Cuenta nueva', 'slug': 'cn'}
    )
    assert Cuenta.cantidad() == 1
    cuenta_nueva = Cuenta.primere()
    assert cuenta_nueva.nombre == 'cuenta nueva'
    assert cuenta_nueva.slug == 'cn'


def test_post_redirige_a_home(client):
    response = client.post(
        reverse('cta_nueva'),
        data={'nombre': 'Cuenta nueva', 'slug': 'cn'}
    )
    asserts.assertRedirects(response, reverse('home'))


def test_cuentas_creadas_son_interactivas(client):
    client.post(
        reverse('cta_nueva'),
        data={'nombre': 'Cuenta nueva', 'slug': 'cn'}
    )
    cuenta_nueva = Cuenta.primere()
    assert cuenta_nueva.get_class() == CuentaInteractiva
