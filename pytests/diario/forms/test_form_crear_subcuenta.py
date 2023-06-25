from unittest.mock import MagicMock

import pytest

from diario.forms import FormCrearSubcuenta
from diario.models import CuentaAcumulativa, CuentaInteractiva, Titular


@pytest.fixture
def formsubcuenta(cuenta_acumulativa: CuentaAcumulativa) -> FormCrearSubcuenta:
    return FormCrearSubcuenta(
        data={
            'nombre': 'subcuenta nueva',
            'slug': 'sn',
        },
        cuenta=cuenta_acumulativa.slug
    )


@pytest.fixture
def mock_agregar_subcuenta(mocker) -> MagicMock:
    return mocker.patch('diario.forms.CuentaAcumulativa.agregar_subcuenta')


def test_llama_a_agregar_subcuenta(mock_agregar_subcuenta, formsubcuenta):
    formsubcuenta.is_valid()
    formsubcuenta.save()
    mock_agregar_subcuenta.assert_called_once()


def test_cuenta_creada_es_subcuenta_de_cuenta(formsubcuenta, cuenta_acumulativa):
    formsubcuenta.is_valid()
    formsubcuenta.save()
    subcuenta = CuentaInteractiva.tomar(slug=formsubcuenta.data['slug'])
    assert subcuenta.cta_madre == cuenta_acumulativa


def test_devuelve_cuenta_madre(formsubcuenta, cuenta_acumulativa):
    formsubcuenta.is_valid()
    cuenta = formsubcuenta.save()
    assert cuenta == cuenta_acumulativa


def test_muestra_campo_titular(formsubcuenta):
    assert 'titular' in formsubcuenta.fields.keys()


def test_muestra_todos_los_titulares_en_campo_titular(formsubcuenta, otro_titular, titular_gordo):
    assert \
        [x[1] for x in formsubcuenta.fields['titular'].choices] == \
        [t.nombre for t in Titular.todes()]


def test_muestra_por_defecto_titular_original_de_cuenta_madre(
        formsubcuenta, cuenta_acumulativa, otro_titular, titular_gordo):
    assert \
        formsubcuenta.fields['titular'].initial == \
        cuenta_acumulativa.titular_original


def test_pasa_datos_correctamente_al_salvar_form(
        mock_agregar_subcuenta, formsubcuenta, otro_titular):
    formsubcuenta.data['titular'] = otro_titular
    formsubcuenta.is_valid()
    formsubcuenta.save()

    mock_agregar_subcuenta.assert_called_once_with(
        'subcuenta nueva', 'sn', otro_titular
    )
