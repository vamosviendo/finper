import pytest


from diario.forms import FormMoneda
from diario.models import Moneda


@pytest.fixture
def formmon() -> FormMoneda:
    return FormMoneda()


@pytest.fixture
def formmon_full() -> FormMoneda:
    return FormMoneda(data={
        'nombre': 'nombre',
        'monname': 'monname',
        'plural': 'monnames',
        'cotizacion': 5.0
    })


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
