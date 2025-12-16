from typing import Dict
from unittest.mock import MagicMock

import pytest
from django.urls import reverse
from pytest_django import asserts

from diario.forms import FormCrearSubcuenta
from utils.iterables import dict2querydict


# Fixtures

@pytest.fixture
def mock_form_crear_subcuenta(mocker, patch_save) -> MagicMock:
    return mocker.patch('diario.views.FormCrearSubcuenta', new_callable=patch_save)


@pytest.fixture
def data() -> Dict[str, str]:
    return {'nombre': 'subcuenta 3', 'sk': 'sc3'}


# Tests

def test_usa_template_agregar_subcuenta(client, cuenta_acumulativa):
    response = client.get(
        reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk])
    )
    asserts.assertTemplateUsed(response, 'diario/cta_agregar_subc.html')


def test_GET_muestra_form_FormCrearSubcuenta_vacio(
        client, cuenta_acumulativa, mock_form_crear_subcuenta):
    client.get(reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk]))
    mock_form_crear_subcuenta.assert_called_once_with(
        cuenta=cuenta_acumulativa.sk)


def test_pasa_form_crear_subcuenta_a_template(client, cuenta_acumulativa):
    response = client.get(
        reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk]))

    assert isinstance(response.context['form'], FormCrearSubcuenta)


def test_POST_pasa_datos_y_cta_original_a_form_subcuentas(
        client, cuenta_acumulativa, data, mock_form_crear_subcuenta):
    client.post(
        reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk]),
        data=data
    )

    mock_form_crear_subcuenta.assert_called_once_with(
        data=dict2querydict(data),
        cuenta=cuenta_acumulativa.sk,
    )


def test_POST_con_datos_validos_guarda_form(
        client, cuenta_acumulativa, data, mock_form_crear_subcuenta):
    falso_form = mock_form_crear_subcuenta.return_value
    falso_form.is_valid.return_value = True

    client.post(
        reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk]),
        data=data
    )

    falso_form.save.assert_called_once()


def test_POST_con_datos_no_validos_no_guarda_form(
        client, cuenta_acumulativa, data, mock_form_crear_subcuenta):
    falso_form = mock_form_crear_subcuenta.return_value
    falso_form.is_valid.return_value = False

    client.post(
        reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk]),
        data=data
    )
    assert not falso_form.save.called


def test_POST_con_form_valido_redirige_a_pag_de_cuenta(
        client, cuenta_acumulativa, data, mock_form_crear_subcuenta):
    falso_form = mock_form_crear_subcuenta.return_value
    falso_form.is_valid.return_value = True
    falso_form.save.return_value = cuenta_acumulativa

    response = client.post(
        reverse('cta_agregar_subc', args=[cuenta_acumulativa.sk]),
        data=data
    )

    asserts.assertRedirects(response, cuenta_acumulativa.get_absolute_url())
