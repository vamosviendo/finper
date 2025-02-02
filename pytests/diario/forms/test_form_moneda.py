import pytest


from diario.forms import FormMoneda
from diario.models import Moneda


@pytest.fixture
def formmon() -> FormMoneda:
    return FormMoneda()


@pytest.fixture
def formmon_data(request) -> dict:
    return {
        'nombre': 'nombre',
        'monname': 'monname',
        'plural': 'monnames',
        'cotizacion_compra': 5.0,
        'cotizacion_venta': 6.0,
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


def test_muestra_campos_cotizacion_compra_y_venta(formmon):
    assert 'cotizacion_compra' in formmon.fields.keys()
    assert 'cotizacion_venta' in formmon.fields.keys()


def test_guarda_cotizaciones_compra_y_venta(formmon_data):
    form = FormMoneda(data=formmon_data)

    form.is_valid()
    form.clean()
    form.save()

    moneda = Moneda.tomar(monname='monname')
    assert moneda.cotizacion_compra == 5.0
    assert moneda.cotizacion_venta == 6.0


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_guarda_cotizacion_1_por_defecto(sentido, formmon_data):
    formmon_data.pop(f"cotizacion_{sentido}")
    form = FormMoneda(data=formmon_data)

    form.is_valid()
    form.clean()
    form.save()

    moneda = Moneda.tomar(monname='monname')
    assert getattr(moneda, f"cotizacion_{sentido}") == 1.0


def test_permite_campo_plural_vacio(formmon_data):
    formmon_data.pop('plural')
    form = FormMoneda(data=formmon_data)
    assert form.is_valid(), f"Form no válido: {form.errors.as_data()}"
