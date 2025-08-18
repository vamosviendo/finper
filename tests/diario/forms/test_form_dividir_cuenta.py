from datetime import date
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from django.forms import fields, DateInput

from diario.forms import FormDividirCuenta
from diario.models import CuentaInteractiva, Titular


@pytest.fixture
def form(cuenta_con_saldo: CuentaInteractiva, otro_titular: Titular, fecha: date) -> FormDividirCuenta:
    return FormDividirCuenta(
        data={
            'fecha': fecha,
            'form_0_nombre': 'Subcuenta 1',
            'form_0_sk': 'sc1',
            'form_0_saldo': 50,
            'form_0_titular': cuenta_con_saldo.titular,
            'form_1_nombre': 'Subcuenta 2',
            'form_1_sk': 'sc2',
            'form_1_saldo': cuenta_con_saldo.saldo() - 50,
            'form_1_titular': otro_titular,
            'form_1_esgratis': True,
        },
        cuenta=cuenta_con_saldo.sk,
    )


@pytest.fixture
def subcuentas(cuenta_con_saldo: CuentaInteractiva, otro_titular: Titular) -> List[Dict[str, Any]]:
    return [
            {
                'nombre': 'Subcuenta 1',
                'sk': 'sc1',
                'saldo': 50.0,
                'titular': cuenta_con_saldo.titular,
                'esgratis': False,
            }, {
                'nombre': 'Subcuenta 2',
                'sk': 'sc2',
                'saldo': cuenta_con_saldo.saldo() - 50.0,
                'titular': otro_titular,
                'esgratis': True,
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


def test_save_divide_cuenta(mocker, form, cuenta_con_saldo, subcuentas, fecha):
    mock_dividir_entre = mocker.patch('diario.forms.CuentaInteractiva.dividir_entre', autospec=True)
    form.is_valid()
    form.save()
    mock_dividir_entre.assert_called_once_with(cuenta_con_saldo, *subcuentas, fecha=fecha)


def test_save_llama_a_clean(mocker, form, subcuentas):
    mock_clean = mocker.patch('diario.forms.FormDividirCuenta.clean')

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
    form.data.pop('form_1_saldo')
    assert form.is_valid()


def test_no_acepta_mas_de_un_campo_saldo_vacio(form):
    form.data.pop('form_0_saldo')
    form.data.pop('form_1_saldo')
    assert not form.is_valid()


def test_muestra_campos_titular(form):
    assert 'form_0_titular' in form.fields.keys()
    assert 'form_1_titular' in form.fields.keys()


def test_muestra_todos_los_titulares_en_campo_titular(
        form, otro_titular, titular_gordo):
    nombres = [t.nombre for t in Titular.todes()]
    assert \
        [x[1] for x in form.fields['form_0_titular'].choices] == nombres
    assert \
        [x[1] for x in form.fields['form_1_titular'].choices] == nombres


def test_muestra_por_defecto_titular_de_cuenta_madre(
        form, cuenta, otro_titular, titular_gordo):
    assert form.fields['form_0_titular'].initial == cuenta.titular


def test_no_muestra_opcion_nula_en_campo_titular(form):
    assert '' not in [x[0] for x in form.fields['form_0_titular'].choices]


def test_pasa_titulares_correctamente_al_salvar_form(
        mock_dividir_y_actualizar, form, otro_titular):
    form.data.update({'form_1_titular': otro_titular})
    form.is_valid()
    form.save()
    assert mock_dividir_y_actualizar.call_args[0][1]['titular'] == otro_titular


def test_muestra_campo_esgratis(form):
    assert 'form_0_esgratis' in form.fields.keys()
    assert 'form_1_esgratis' in form.fields.keys()
    assert isinstance(form.fields['form_0_esgratis'], fields.BooleanField)


def test_campo_esgratis_no_seleccionado_por_defecto(form):
    assert form.fields['form_0_esgratis'].initial is False


def test_campo_esgratis_seleccionado_en_subcuenta_con_otro_titular_no_genera_movimiento_credito(
        mock_crear_movimiento_credito, form, otro_titular):

    form.data.update({'form_1_titular': otro_titular})
    form.data.update({'form_1_esgratis': True})
    form.full_clean()
    form.save()
    mock_crear_movimiento_credito.assert_not_called()


def test_campo_esgratis_no_seleccionado_en_subcuenta_con_otro_titular_genera_movimiento_credito(
        mock_crear_movimiento_credito, form, otro_titular):
    form.data.update({'form_1_titular': otro_titular})
    form.data.update({'form_1_esgratis': False})
    form.full_clean()
    mov = form.save().subcuentas.last().movs()[0]
    mock_crear_movimiento_credito.assert_called_once_with(mov)


def test_muestra_campo_fecha(form):
    assert 'fecha' in form.fields.keys()


def test_campo_fecha_muestra_fecha_de_hoy_por_defecto(form):
    assert form.fields['fecha'].initial == date.today()


def test_campo_fecha_usa_widget_de_seleccion_de_fecha(form):
    assert type(form.fields['fecha'].widget) == DateInput
