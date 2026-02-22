import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.models import Cuenta


# Fixtures

@pytest.fixture
def full_url(cuenta: Cuenta, cuenta_2: Cuenta) -> str:
    return f"{reverse('corregir_saldo')}?ctas={cuenta.sk}!{cuenta_2.sk}"


# Tests

def test_usa_template_corregir_saldo(client, full_url):
    response = client.get(full_url)
    asserts.assertTemplateUsed(response, 'diario/corregir_saldo.html')


def test_redirige_a_home_si_no_recibe_querystring_o_con_querystring_mal_formada(client):
    url1 = reverse('corregir_saldo')
    url2 = f"{reverse('corregir_saldo')}?ctas="
    url3 = f"{reverse('corregir_saldo')}?ctas=a"
    url4 = f"{reverse('corregir_saldo')}?cuculo=2"
    asserts.assertRedirects(client.get(url1), reverse('home'))
    asserts.assertRedirects(client.get(url2), reverse('home'))
    asserts.assertRedirects(client.get(url3), reverse('home'))
    asserts.assertRedirects(client.get(url4), reverse('home'))


def test_pasa_lista_de_cuentas_erroneas_a_template(
        client, full_url, cuenta, cuenta_2, cuenta_3):
    response = client.get(full_url)
    assert response.context['ctas_erroneas'] == [cuenta, cuenta_2]
