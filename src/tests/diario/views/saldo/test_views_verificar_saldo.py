from unittest.mock import MagicMock

import pytest
from django.urls import reverse
from pytest_django import asserts


# Fixtures

@pytest.fixture
def mock_verificar_saldos(mocker) -> MagicMock:
    return mocker.patch('diario.views.verificar_saldos')


# Tests

def test_verifica_saldo_de_cuentas(client, mock_verificar_saldos):
    client.get(reverse('verificar_saldos'))
    mock_verificar_saldos.assert_called_once()


def test_redirige_a_home_si_no_hay_saldos_erroneos(client, mock_verificar_saldos):
    mock_verificar_saldos.return_value = []
    response = client.get(reverse('verificar_saldos'))
    asserts.assertRedirects(response, reverse('home'))


def test_redirige_a_corregir_saldo_si_hay_saldos_erroneos(
        client, mock_verificar_saldos, cuenta, cuenta_2):
    mock_verificar_saldos.return_value = [cuenta, cuenta_2]

    response = client.get(reverse('verificar_saldos'))

    asserts.assertRedirects(
        response,
        reverse('corregir_saldo') + f'?ctas={cuenta.sk}!{cuenta_2.sk}',
    )


def test_pasa_cuentas_con_saldo_erroneo_a_corregir_saldo(
        client, mock_verificar_saldos, cuenta, cuenta_2, cuenta_3):
    mock_verificar_saldos.return_value = [cuenta, cuenta_2]

    response = client.get(reverse('verificar_saldos'))

    assert cuenta.sk in response.url
    assert cuenta_2.sk in response.url
    assert cuenta_3.sk not in response.url
