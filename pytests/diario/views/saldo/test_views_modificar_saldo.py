import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.models import Cuenta
from utils.helpers_tests import dividir_en_dos_subcuentas


@pytest.fixture
def full_url(cuenta: Cuenta, cuenta_2: Cuenta) -> str:
    return f"{reverse('modificar_saldo', args=[cuenta.sk])}" \
           f"?ctas={cuenta.sk}!{cuenta_2.sk}"


def test_redirige_a_corregir_saldo_con_ctas_erroneas_menos_la_corregida(
        client, full_url, cuenta_2):
    response = client.get(full_url)
    asserts.assertRedirects(
        response,
        f"{reverse('corregir_saldo')}?ctas={cuenta_2.sk}"
    )


def test_redirige_a_home_si_es_la_unica_cuenta_erronea(client, cuenta_2):
    response = client.get(
        f"{reverse('modificar_saldo', args=[cuenta_2.sk])}"
        f"?ctas={cuenta_2.sk}"
    )
    asserts.assertRedirects(response, f"{reverse('home')}")


def test_corrige_saldo_de_cuenta_interactiva(client, mocker, full_url, cuenta):
    mock_cta_corregir_saldo = mocker.patch(
        'diario.views.CuentaInteractiva.corregir_saldo',
        autospec=True
    )
    client.get(full_url)
    mock_cta_corregir_saldo.assert_called_once_with(cuenta)


def test_no_admite_cuenta_acumulativa(client, full_url, cuenta):
    dividir_en_dos_subcuentas(cuenta)
    with pytest.raises(AttributeError):
        client.get(full_url)
