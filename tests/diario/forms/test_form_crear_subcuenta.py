from datetime import date
from unittest.mock import MagicMock

import pytest
from django import forms

from diario.forms import FormCrearSubcuenta
from diario.models import CuentaAcumulativa, CuentaInteractiva, Titular


@pytest.fixture
def formsubcuenta(cuenta_acumulativa: CuentaAcumulativa) -> FormCrearSubcuenta:
    return FormCrearSubcuenta(
        data={
            'nombre': 'subcuenta nueva',
            'sk': 'sn',
        },
        cuenta=cuenta_acumulativa.sk
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
    subcuenta = CuentaInteractiva.tomar(sk=formsubcuenta.data['sk'])
    assert subcuenta.cta_madre == cuenta_acumulativa


def test_devuelve_cuenta_madre(formsubcuenta, cuenta_acumulativa):
    formsubcuenta.is_valid()
    cuenta = formsubcuenta.save()
    assert cuenta == cuenta_acumulativa


def test_muestra_campo_fecha(formsubcuenta):
    assert 'fecha' in formsubcuenta.fields.keys()


def test_campo_fecha_usa_widget_DateInput(formsubcuenta):
    field_fecha = formsubcuenta.fields['fecha']
    assert isinstance(field_fecha.widget, forms.DateInput)
    assert field_fecha.widget.format == '%Y-%m-%d'


def test_campo_fecha_muestra_fecha_de_hoy_por_defecto(formsubcuenta):
    assert formsubcuenta.fields['fecha'].initial == date.today()


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


def test_agrega_subcuenta_con_nombre_sk_titular_y_fecha_ingresados(
        mock_agregar_subcuenta, formsubcuenta, otro_titular, fecha):
    formsubcuenta.data['titular'] = otro_titular
    formsubcuenta.data['fecha'] = fecha
    formsubcuenta.is_valid()
    formsubcuenta.save()

    mock_agregar_subcuenta.assert_called_once_with(
        nombre='subcuenta nueva', sk='sn', titular=otro_titular, fecha=fecha
    )
