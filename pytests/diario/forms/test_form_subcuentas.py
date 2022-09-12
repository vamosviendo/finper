from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from django.forms import fields

from diario.forms import FormSubcuentas
from diario.models import CuentaInteractiva, Titular


@pytest.fixture
def form(cuenta_con_saldo: CuentaInteractiva) -> FormSubcuentas:
    return FormSubcuentas(
        data={
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-nombre': 'Subcuenta 1',
            'form-0-slug': 'sc1',
            'form-0-saldo': 50,
            'form-1-nombre': 'Subcuenta 2',
            'form-1-slug': 'sc2',
            'form-1-saldo': cuenta_con_saldo.saldo - 50,
        },
        cuenta=cuenta_con_saldo.slug,
    )


@pytest.fixture
def subcuentas(cuenta_con_saldo: CuentaInteractiva) -> List[Dict[str, Any]]:
    return [
            {
                'nombre': 'Subcuenta 1',
                'slug': 'sc1',
                'saldo': 50.0,
                'titular': cuenta_con_saldo.titular,
                'esgratis': False,
            }, {
                'nombre': 'Subcuenta 2',
                'slug': 'sc2',
                'saldo': cuenta_con_saldo.saldo - 50.0,
                'titular': cuenta_con_saldo.titular,
                'esgratis': False,
            },
        ]


@pytest.fixture
def mock_crear_movimiento_credito(mocker) -> MagicMock:
    return mocker.patch(
        'diario.forms.Movimiento._crear_movimiento_credito', autospec=True
    )


@pytest.fixture
def mock_dividir_y_actualizar(mocker) -> MagicMock:
    return mocker.patch(
        'diario.forms.CuentaInteractiva.dividir_y_actualizar'
    )


def test_save_divide_cuenta(mocker, form, subcuentas):
    mock_dividir_entre = mocker.patch('diario.forms.CuentaInteractiva.dividir_entre')
    form.is_valid()
    form.save()
    mock_dividir_entre.assert_called_once_with(*subcuentas, fecha=None)


def test_save_llama_a_clean(mocker, form, subcuentas):
    mock_clean = mocker.patch('diario.forms.FormSubcuentas.clean')

    def side_effect():
        form.subcuentas = subcuentas
    mock_clean.side_effect = side_effect

    form.is_valid()
    form.save()
    mock_clean.assert_called_once()


def test_save_devuelve_cuenta_madre(mock_dividir_y_actualizar, cuenta_con_saldo, form):
    mock_dividir_y_actualizar.return_value = cuenta_con_saldo
    form.is_valid()
    cuenta = form.save()
    assert cuenta == cuenta_con_saldo


def test_acepta_un_campo_saldo_vacio(form):
    form.data.pop('form-1-saldo')
    assert form.is_valid()


def test_no_acepta_mas_de_un_campo_saldo_vacio(form):
    form.data.pop('form-0-saldo')
    form.data.pop('form-1-saldo')
    assert not form.is_valid()


def test_muestra_campo_titular(form):
    for f in form.forms:
        assert 'titular' in f.fields.keys()


def test_muestra_todos_los_titulares_en_campo_titular(
        form, otro_titular, titular_gordo):
    assert \
        [x[1] for x in form.forms[0].fields['titular'].choices] == \
        [t.nombre for t in Titular.todes()]


def test_muestra_por_defecto_titular_de_cuenta_madre(
        form, cuenta, otro_titular, titular_gordo):
    assert form.forms[0].fields['titular'].initial == cuenta.titular


def test_no_muestra_opcion_nula_en_campo_titular(form):
    assert '' not in [x[0] for x in form.forms[0].fields['titular'].choices]


def test_pasa_titulares_correctamente_al_salvar_form(
        mock_dividir_y_actualizar, form, otro_titular):
    form.data.update({'form-1-titular': otro_titular})
    form.is_valid()
    form.save()
    assert mock_dividir_y_actualizar.call_args[0][1]['titular'] == otro_titular


def test_muestra_campo_esgratis(form):
    assert 'esgratis' in form.forms[0].fields.keys()
    assert isinstance(form.forms[0].fields['esgratis'], fields.BooleanField)


def test_campo_esgratis_no_seleccionado_por_defecto(form):
    assert form.forms[0].fields['esgratis'].initial is False


def test_campo_esgratis_seleccionado_en_subcuenta_con_otro_titular_no_genera_movimiento_credito(
        mock_crear_movimiento_credito, form, otro_titular):

    form.data.update({'form-1-titular': otro_titular})
    form.data.update({'form-1-esgratis': True})
    form.full_clean()
    form.save()
    mock_crear_movimiento_credito.assert_not_called()


def test_campo_esgratis_no_seleccionado_en_subcuenta_con_otro_titular_genera_movimiento_credito(
        mock_crear_movimiento_credito, form, otro_titular):
    form.data.update({'form-1-titular': otro_titular})
    form.data.update({'form-1-esgratis': False})
    form.full_clean()
    mov = form.save().subcuentas.last().movs()[0]
    mock_crear_movimiento_credito.assert_called_once_with(mov)
