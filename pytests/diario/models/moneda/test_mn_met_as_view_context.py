import pytest


@pytest.fixture
def context(peso):
    return peso.as_view_context()


def test_incluye_monname(context, peso):
    assert context.get('monname') is not None
    assert context['monname'] == peso.monname


def test_incluye_nombre(context, peso):
    assert context.get('nombre') is not None
    assert context['nombre'] == peso.nombre


def test_incluye_cotizacion_venta_como_cotizacion(context, peso):
    assert context.get('cotizacion') is not None
    assert context['cotizacion'] == peso.cotizacion_venta
