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
        'sk': 'sk',
        'plural': 'sks',
        'cotizacion_compra': 5.0,
        'cotizacion_venta': 6.0,
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


def test_muestra_campos_cotizacion_compra_y_venta(formmon):
    assert 'cotizacion_compra' in formmon.fields.keys()
    assert 'cotizacion_venta' in formmon.fields.keys()


def test_guarda_cotizaciones_compra_y_venta(formmon_data):
    form = FormMoneda(data=formmon_data)

    form.is_valid()
    form.clean()
    form.save()

    moneda = Moneda.tomar(sk='sk')
    assert moneda.cotizacion_compra == 5.0
    assert moneda.cotizacion_venta == 6.0


@pytest.mark.parametrize("sentido", ["compra", "venta"])
def test_guarda_cotizacion_1_por_defecto(sentido, formmon_data):
    formmon_data.pop(f"cotizacion_{sentido}")
    form = FormMoneda(data=formmon_data)

    form.is_valid()
    form.clean()
    form.save()

    moneda = Moneda.tomar(sk='sk')
    assert getattr(moneda, f"cotizacion_{sentido}") == 1.0


def test_muestra_al_inicio_sk_de_moneda_asociada(dolar):
    f = FormMoneda(instance=dolar)
    assert f.fields["sk"].initial == dolar.sk


def test_permite_campo_plural_vacio(formmon_data):
    formmon_data.pop('plural')
    form = FormMoneda(data=formmon_data)
    assert form.is_valid(), f"Form no válido: {form.errors.as_data()}"
