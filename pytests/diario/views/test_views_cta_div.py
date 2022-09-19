from unittest.mock import MagicMock

import pytest
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from pytest_django import asserts

from diario.models import Cuenta, CuentaInteractiva
from diario.views import cta_div_view


@pytest.fixture
def mock_form_subcuentas(mocker, patch_save) -> MagicMock:
    return mocker.patch('diario.views.FormSubcuentas', new_callable=patch_save)


@pytest.fixture
def mock_render(mocker) -> MagicMock:
    return mocker.patch('diario.views.render')


@pytest.fixture
def request_2_subcuentas() -> HttpRequest:
    req = HttpRequest()
    req.method = 'POST'
    req.POST['form-TOTAL_FORMS'] = 2
    req.POST['form-INITIAL_FORMS'] = 0
    req.POST['form-0-nombre'] = 'Subcuenta 1'
    req.POST['form-0-slug'] = 'sc1'
    req.POST['form-0-saldo'] = 50
    req.POST['form-1-nombre'] = 'Subcuenta 2'
    req.POST['form-1-slug'] = 'sc2'
    req.POST['form-1-saldo'] = 200
    return req


@pytest.fixture
def int_response(client, cuenta_con_saldo: CuentaInteractiva) -> HttpResponse:
    return client.post(
        reverse('cta_div', args=[cuenta_con_saldo.slug]),
        data={
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-nombre': 'Subcuenta 1',
            'form-0-slug': 'sc1',
            'form-0-saldo': 50,
            'form-1-nombre': 'Subcuenta 2',
            'form-1-slug': 'sc2',
            'form-1-saldo': cuenta_con_saldo.saldo - 50,
        }
    )


def test_usa_template_cta_div_formset(client, cuenta):
    response = client.get(reverse('cta_div', args=[cuenta.slug]))
    asserts.assertTemplateUsed(response, 'diario/cta_div_formset.html')


def test_muestra_form_subcuentas_al_acceder_a_pagina(
        client, cuenta, mock_render, mock_form_subcuentas):
    falso_form = mock_form_subcuentas.return_value
    request = HttpRequest()
    request.method = 'GET'

    cta_div_view(request, slug=cuenta.slug)

    mock_form_subcuentas.assert_called_once_with(cuenta=cuenta.slug)
    mock_render.assert_called_once_with(
        request,
        'diario/cta_div_formset.html',
        {'formset': falso_form}
    )


def test_pasa_datos_post_y_cta_original_a_form_subcuentas(
        client, cuenta, mock_form_subcuentas, request_2_subcuentas):
    cta_div_view(request_2_subcuentas, slug=cuenta.slug)
    mock_form_subcuentas.assert_called_with(
        data=request_2_subcuentas.POST,
        cuenta=cuenta.slug,
    )


def test_guarda_form_si_los_datos_son_validos(
        client, cuenta, mock_form_subcuentas, request_2_subcuentas):
    falso_form = mock_form_subcuentas.return_value
    falso_form.is_valid.return_value = True

    cta_div_view(request_2_subcuentas, slug=cuenta.slug)

    falso_form.save.assert_called_once()


def test_redirige_a_destino_si_el_form_es_valido(
        client, cuenta, mocker, mock_form_subcuentas, request_2_subcuentas):
    mock_redirect = mocker.patch('diario.views.redirect')
    falso_form = mock_form_subcuentas.return_value
    falso_form.is_valid.return_value = True

    response = cta_div_view(request_2_subcuentas, slug=cuenta.slug)
    assert response == mock_redirect.return_value
    mock_redirect.assert_called_once_with(falso_form.save.return_value)


def test_no_guarda_form_si_los_datos_no_son_validos(
        client, cuenta, mock_form_subcuentas, request_2_subcuentas):
    falso_form = mock_form_subcuentas.return_value
    falso_form.is_valid.return_value = False

    cta_div_view(request_2_subcuentas, slug=cuenta.slug)
    assert not falso_form.save.called


def test_vuelve_a_mostrar_template_y_form_con_form_no_valido(
        client, cuenta, mock_render, mock_form_subcuentas, request_2_subcuentas):
    falso_form = mock_form_subcuentas.return_value
    falso_form.is_valid.return_value = False

    response = cta_div_view(request_2_subcuentas, slug=cuenta.slug)

    assert response == mock_render.return_value
    mock_render.assert_called_once_with(
        request_2_subcuentas,
        'diario/cta_div_formset.html',
        {'formset': falso_form},
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
        reverse('cta_detalle', args=[cuenta_con_saldo.slug]),
    )
