import pytest
from django import forms

from diario.forms import FormTitular


@pytest.fixture
def formtit() -> FormTitular:
    return FormTitular()


def test_muestra_campo_nombre(formtit):
    assert 'nombre' in formtit.fields.keys()


def test_muestra_campo_titname(formtit):
    assert 'titname' in formtit.fields.keys()


def test_muestra_campo_fecha_alta(formtit):
    assert 'fecha_alta' in formtit.fields.keys()


def test_campo_fecha_alta_usa_widget_DateInput(formtit):
    field_fecha_alta = formtit.fields['fecha_alta']
    assert isinstance(field_fecha_alta.widget, forms.DateInput)
    assert field_fecha_alta.widget.format == '%Y-%m-%d'
