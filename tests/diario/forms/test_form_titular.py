import pytest
from django import forms

from diario.forms import FormTitular
from diario.models import Titular


@pytest.fixture
def formtit() -> FormTitular:
    return FormTitular()


@pytest.fixture
def formtit_data(fecha) -> dict:
    return {
        'nombre': 'nombre',
        'sk': 'sk',
        'fecha_alta': fecha,
    }


@pytest.fixture
def formtit_full(formtit_data):
    return FormTitular(data=formtit_data)


@pytest.mark.parametrize("campo", Titular.form_fields)
def test_muestra_campos_necesarios(formtit, campo):
    assert campo in formtit.fields.keys()


def test_campo_fecha_alta_usa_widget_DateInput(formtit):
    field_fecha_alta = formtit.fields['fecha_alta']
    assert isinstance(field_fecha_alta.widget, forms.DateInput)
    assert field_fecha_alta.widget.format == '%Y-%m-%d'


def test_guarda_campo_sk(formtit_full, fecha):
    formtit_full.full_clean()
    formtit_full.save()
    try:
        t = Titular.tomar(sk = "sk")
    except Titular.DoesNotExist:
        raise AssertionError("No se guardó sk")
    assert t.nombre == "nombre"
    assert t.fecha_alta == fecha


def test_muestra_al_inicio_sk_de_titular_asociado(titular):
    f = FormTitular(instance=titular)
    assert f.fields["sk"].initial == titular.sk
