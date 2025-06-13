from datetime import date

import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.models import Titular, Cuenta, CuentaInteractiva


@pytest.fixture(autouse=True)
def titular_principal(titular_principal):
    return titular_principal


@pytest.fixture
def post_data(fecha: date) -> dict:
    return {'nombre': 'Cuenta nueva', 'sk': 'cn', 'fecha_creacion': fecha}


def test_si_no_hay_titulares_redirige_a_crear_titular_con_get(client):
    Titular.todes().delete()
    response = client.get(reverse('cta_nueva'))
    asserts.assertRedirects(response, reverse('tit_nuevo'))


def test_usa_template_cta_form(client):
    response = client.get(reverse('cta_nueva'))
    asserts.assertTemplateUsed(response, 'diario/cta_form.html')


def test_post_guarda_cuenta_nueva(client, post_data):
    client.post(
        reverse('cta_nueva'),
        data=post_data
    )
    assert Cuenta.cantidad() == 1
    cuenta_nueva = Cuenta.primere()
    assert cuenta_nueva.nombre == 'cuenta nueva'
    assert cuenta_nueva.sk == 'cn'


def test_post_redirige_a_url_recibida_en_querystring(client, titular, post_data):
    response = client.post(
        reverse('cta_nueva') + f"?next=/diario/t/{titular.sk}/",
        data=post_data
    )
    asserts.assertRedirects(response, f"/diario/t/{titular.sk}/")


def test_post_redirige_a_home_si_no_recibe_url_en_queryset(client, post_data):
    response = client.post(
        reverse('cta_nueva'),
        data=post_data
    )
    asserts.assertRedirects(response, reverse('home'))


def test_cuentas_creadas_son_interactivas(client, post_data):
    client.post(
        reverse('cta_nueva'),
        data=post_data
    )
    cuenta_nueva = Cuenta.primere()
    assert cuenta_nueva.get_class() == CuentaInteractiva
