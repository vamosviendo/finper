import pytest

from django import forms
from django.utils import timezone

from diario.forms import FormCuenta
from diario.models import Titular, Moneda, Cuenta


@pytest.fixture(autouse=True)
def mock_titular_principal(mocker, titular):
    return mocker.patch('diario.forms.TITULAR_PRINCIPAL', titular.sk)


def test_muestra_campo_sk():
    f = FormCuenta()
    assert "sk" in f.fields.keys()


def test_no_acepta_cuentas_sin_sk():
    formcta = FormCuenta(data={'nombre': 'Efectivo'})
    assert not formcta.is_valid()


def test_no_acepta_guion_bajo_inicial_en_sk():
    formcta = FormCuenta(data={'nombre': '_Efectivo', 'sk': '_efe'})
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
    assert formcta.fields['moneda'].initial == Moneda.tomar(sk=mock_moneda_base)


def test_guarda_sk(titular, fecha):
    formcta = FormCuenta(data={
        "sk": "clave",
        "nombre": "cuenta",
        "fecha_creacion": fecha,
        "titular": titular,
    })
    formcta.is_valid()
    formcta.full_clean()
    try:
        formcta.save()
    except ValueError:
        print(f"ERRORS: {formcta.errors}")
        raise AssertionError("No puede crear cuenta interactiva")

    try:
        c = Cuenta.tomar(sk="clave")
    except Cuenta.DoesNotExist:
        raise AssertionError("No guarda sk")
    assert c.nombre == "cuenta"


def test_muestra_al_inicio_sk_de_cuenta_asociada(cuenta):
    formcta = FormCuenta(instance=cuenta)
    assert formcta.fields["sk"].initial == cuenta.sk
