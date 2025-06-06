from unittest.mock import MagicMock

import pytest
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from pytest_django import asserts

from diario.models import Cuenta, CuentaInteractiva
from diario.views import cta_div_view


@pytest.fixture
def mock_form_dividir_cuenta(mocker, patch_save) -> MagicMock:
    return mocker.patch('diario.views.FormDividirCuenta', new_callable=patch_save)


@pytest.fixture
def mock_render(mocker) -> MagicMock:
    return mocker.patch('diario.views.render')


@pytest.fixture
def request_2_subcuentas() -> HttpRequest:
    req = HttpRequest()
    req.method = 'POST'
    req.POST['form_0_nombre'] = 'Subcuenta 1'
    req.POST['form_0_sk'] = 'sc1'
    req.POST['form_0_saldo'] = '50'
    req.POST['form_1_nombre'] = 'Subcuenta 2'
    req.POST['form_1_sk'] = 'sc2'
    req.POST['form_1_saldo'] = '200'
    return req


@pytest.fixture
def int_response(client, cuenta_con_saldo: CuentaInteractiva) -> HttpResponse:
    return client.post(
        reverse('cta_div', args=[cuenta_con_saldo.sk]),
        data={
            'form_0_nombre': 'Subcuenta 1',
            'form_0_sk': 'sc1',
            'form_0_saldo': 50,
            'form_1_nombre': 'Subcuenta 2',
            'form_1_sk': 'sc2',
            'form_1_saldo': cuenta_con_saldo.saldo() - 50,
        }
    )


def test_usa_template_cta_div_form(client, cuenta):
    response = client.get(reverse('cta_div', args=[cuenta.sk]))
    asserts.assertTemplateUsed(response, 'diario/cta_div_form.html')


def test_muestra_form_dividir_cuenta_al_acceder_a_pagina(
        client, cuenta, mock_render, mock_form_dividir_cuenta):
    falso_form = mock_form_dividir_cuenta.return_value
    request = HttpRequest()
    request.method = 'GET'

    cta_div_view(request, sk=cuenta.sk)

    mock_form_dividir_cuenta.assert_called_once_with(cuenta=cuenta.sk)
    mock_render.assert_called_once_with(
        request,
        'diario/cta_div_form.html',
        {'form': falso_form}
    )


def test_pasa_datos_post_y_cta_original_a_form_subcuentas(
        client, cuenta, mock_form_dividir_cuenta, request_2_subcuentas):
    cta_div_view(request_2_subcuentas, sk=cuenta.sk)
    mock_form_dividir_cuenta.assert_called_with(
        data=request_2_subcuentas.POST,
        cuenta=cuenta.sk,
    )


def test_guarda_form_si_los_datos_son_validos(
        client, cuenta, mock_form_dividir_cuenta, request_2_subcuentas):
    falso_form = mock_form_dividir_cuenta.return_value
    falso_form.is_valid.return_value = True

    cta_div_view(request_2_subcuentas, sk=cuenta.sk)

    falso_form.save.assert_called_once()


def test_redirige_a_destino_si_el_form_es_valido(
        client, cuenta, mocker, mock_form_dividir_cuenta, request_2_subcuentas):
    mock_redirect = mocker.patch('diario.views.redirect')
    falso_form = mock_form_dividir_cuenta.return_value
    falso_form.is_valid.return_value = True

    response = cta_div_view(request_2_subcuentas, sk=cuenta.sk)
    assert response == mock_redirect.return_value
    mock_redirect.assert_called_once_with(falso_form.save.return_value)


def test_no_guarda_form_si_los_datos_no_son_validos(
        client, cuenta, mock_form_dividir_cuenta, request_2_subcuentas):
    falso_form = mock_form_dividir_cuenta.return_value
    falso_form.is_valid.return_value = False

    cta_div_view(request_2_subcuentas, sk=cuenta.sk)
    assert not falso_form.save.called


def test_vuelve_a_mostrar_template_y_form_con_form_no_valido(
        client, cuenta, mock_render, mock_form_dividir_cuenta, request_2_subcuentas):
    falso_form = mock_form_dividir_cuenta.return_value
    falso_form.is_valid.return_value = False

    response = cta_div_view(request_2_subcuentas, sk=cuenta.sk)

    assert response == mock_render.return_value
    mock_render.assert_called_once_with(
        request_2_subcuentas,
        'diario/cta_div_form.html',
        {'form': falso_form},
    )


def test_integrativo_post_divide_cuenta(cuenta_con_saldo, request):
    cantidad = Cuenta.cantidad()
    request.getfixturevalue('int_response')
    assert Cuenta.cantidad() == cantidad + 2
    assert len([x for x in Cuenta.todes() if x.es_interactiva]) == 2
    assert len([x for x in Cuenta.todes() if x.es_acumulativa]) == 1


def test_integrativo_redirige_a_pagina_de_cuenta(
        client, cuenta_con_saldo, int_response):
    asserts.assertRedirects(
        int_response,
        reverse('cuenta', args=[cuenta_con_saldo.sk]),
    )
