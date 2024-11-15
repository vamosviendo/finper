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
        'monname': 'monname',
        'plural': 'monnames',
        'cotizacion': 5.0
    }


@pytest.fixture
def formmon_full(formmon_data) -> FormMoneda:
    return FormMoneda(data=formmon_data)


def test_muestra_campo_nombre(formmon):
    assert 'nombre' in formmon.fields.keys()


def test_muestra_campo_monname(formmon):
    assert 'monname' in formmon.fields.keys()


def test_muestra_campo_plural(formmon):
    assert 'plural' in formmon.fields.keys()


def test_guarda_campo_plural(formmon_full):
    form = formmon_full
    form.is_valid()
    form.clean()
    form.save()
    moneda = Moneda.tomar(monname='monname')
    assert moneda.plural == 'monnames'


def test_muestra_campo_cotizacion(formmon):
    assert 'cotizacion' in formmon.fields.keys()


def test_guarda_cotizacion(formmon_full):
    form = formmon_full
    form.is_valid()
    form.clean()
    form.save()
    moneda = Moneda.tomar(monname='monname')
    assert moneda.cotizacion == 5.0


def test_permite_campo_plural_vacio(formmon_data):
    formmon_data.pop('plural')
    form = FormMoneda(data=formmon_data)
    assert form.is_valid(), f"Form no válido: {form.errors.as_data()}"


def test_guarda_cotizacion_1_por_defecto(formmon_data):
    formmon_data.pop('cotizacion')
    form = FormMoneda(data=formmon_data)
    form.is_valid()
    form.clean()
    form.save()
    moneda = Moneda.tomar(monname='monname')
    assert moneda.cotizacion == 1.0
