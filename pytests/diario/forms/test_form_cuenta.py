import pytest

from django import forms
from django.utils import timezone

from diario.forms import FormCuenta
from diario.models import Titular, Moneda


@pytest.fixture(autouse=True)
def mock_titular_principal(mocker, titular):
    return mocker.patch('diario.forms.TITULAR_PRINCIPAL', titular.sk)


def test_no_acepta_cuentas_sin_slug():
    formcta = FormCuenta(data={'nombre': 'Efectivo'})
    assert not formcta.is_valid()


def test_no_acepta_guion_bajo_inicial_en_slug():
    formcta = FormCuenta(data={'nombre': '_Efectivo', 'slug': '_efe'})
    assert not formcta.is_valid()


def test_muestra_campo_fecha_creacion():
    formcta = FormCuenta()
    assert 'fecha_creacion' in formcta.fields.keys()


def test_campo_fecha_creacion_usa_widget_DateInput():
    formcta = FormCuenta()
    field_fecha_creacion = formcta.fields['fecha_creacion']
    assert isinstance(field_fecha_creacion.widget, forms.DateInput)
    assert field_fecha_creacion.widget.format == '%Y-%m-%d'


def test_campo_fecha_creacion_muestra_fecha_actual_como_valor_por_defecto():
    formcta = FormCuenta()
    assert formcta.fields['fecha_creacion'].initial == timezone.now().date()


def test_campo_titular_muestra_titular_principal_como_valor_por_defecto(mock_titular_principal):
    formcta = FormCuenta()
    assert formcta.fields['titular'].initial == Titular.tomar(sk=mock_titular_principal)


def test_muestra_campo_moneda():
    formcta = FormCuenta()
    assert 'moneda' in formcta.fields.keys()


def test_campo_moneda_muestra_moneda_base_como_valor_por_defecto(mock_moneda_base):
    formcta = FormCuenta()
    assert formcta.fields['moneda'].initial == Moneda.tomar(monname=mock_moneda_base)
