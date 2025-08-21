import pytest


from diario.forms import FormMoneda
from diario.models import Moneda


@pytest.fixture
def formmon() -> FormMoneda:
    return FormMoneda()


@pytest.fixture
def formmon_data() -> dict:
    return {
        'nombre': 'nombre',
        'sk': 'sk',
        'plural': 'sks',
    }


@pytest.fixture
def formmon_full(formmon_data) -> FormMoneda:
    return FormMoneda(data=formmon_data)


def test_muestra_campo_nombre(formmon):
    assert 'nombre' in formmon.fields.keys()


def test_muestra_campo_sk(formmon):
    assert 'sk' in formmon.fields.keys()


def test_muestra_campo_plural(formmon):
    assert 'plural' in formmon.fields.keys()


def test_guarda_campo_plural(formmon_full):
    form = formmon_full
    form.is_valid()
    form.clean()
    form.save()
    moneda = Moneda.tomar(sk='sk')
    assert moneda.plural == 'sks'


def test_guarda_sk(formmon_full):
    formmon_full.is_valid()
    formmon_full.clean()
    formmon_full.save()
    try:
        m = Moneda.tomar(sk="sk")
    except Moneda.DoesNotExist:
        raise AssertionError("No se guardó sk")
    assert m.nombre == "nombre"


def test_muestra_al_inicio_sk_de_moneda_asociada(dolar):
    f = FormMoneda(instance=dolar)
    assert f.fields["sk"].initial == dolar.sk


def test_permite_campo_plural_vacio(formmon_data):
    formmon_data.pop('plural')
    form = FormMoneda(data=formmon_data)
    assert form.is_valid(), f"Form no válido: {form.errors.as_data()}"
