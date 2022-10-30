import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.models import Cuenta


@pytest.fixture
def full_url(cuenta: Cuenta, cuenta_2: Cuenta) -> str:
    return \
        f"{reverse('agregar_movimiento', args=[cuenta_2.slug])}" \
        f"?ctas={cuenta.slug}!{cuenta_2.slug}"


def test_redirige_a_corregir_saldo_con_ctas_erroneas_menos_la_corregida(
        client, full_url, cuenta):
    response = client.get(full_url)
    asserts.assertRedirects(
        response,
        f"{reverse('corregir_saldo')}?ctas={cuenta.slug}"
    )


def test_redirige_a_home_si_es_la_unica_cuenta_erronea(client, cuenta_2):
    response = client.get(
        f"{reverse('agregar_movimiento', args=[cuenta_2.slug])}"
        f"?ctas={cuenta_2.slug}"
    )
    asserts.assertRedirects(response, f"{reverse('home')}")


def test_agrega_movimiento_para_coincidir_con_saldo(
        client, mocker, full_url, cuenta_2):
    mock_cta_agregar_mov = mocker.patch(
        'diario.views.CuentaInteractiva.agregar_mov_correctivo',
        autospec=True
    )
    client.get(full_url)
    mock_cta_agregar_mov.assert_called_once_with(cuenta_2)


def test_integrativo_agrega_movimiento_para_coincidir_con_saldo(
        client, cuenta_2, entrada_otra_cuenta, full_url):
    cant_movs = cuenta_2.cantidad_movs()
    saldo = cuenta_2.ultimo_saldo
    saldo.importe = 135
    saldo.save()

    client.get(full_url)

    assert cuenta_2.cantidad_movs() == cant_movs + 1
    assert cuenta_2.saldo == saldo.importe
