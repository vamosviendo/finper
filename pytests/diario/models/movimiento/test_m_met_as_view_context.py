import pytest

from diario.models import Movimiento


@pytest.fixture
def context(entrada):
    return entrada.as_view_context()


def test_incluye_id_de_movimiento(entrada, context):
    assert context.get('pk') is not None
    assert context['pk'] == entrada.pk


def test_incluye_concepto_de_movimiento(entrada, context):
    assert context.get('concepto') is not None
    assert context['concepto'] == entrada.concepto


def test_incluye_detalle_de_movimiento(entrada):
    entrada.detalle = 'Detalle de entrada'
    entrada.save()
    context = entrada.as_view_context()
    assert context.get('detalle') is not None
    assert context['detalle'] == 'Detalle de entrada'


def test_incluye_fecha_de_movimiento(entrada, context):
    assert context.get('fecha') is not None
    assert context['fecha'] == entrada.fecha


def test_incluye_importe_de_movimiento(entrada, context):
    assert context.get('importe') is not None
    assert context['importe'] == entrada.importe


def test_incluye_string_con_cuentas_de_movimiento(entrada, context):
    assert context.get('str_cuentas') is not None
    assert context['str_cuentas'] == entrada.str_cuentas()


def test_incluye_indicador_de_movimiento_automatico(entrada, credito):
    e_context = entrada.as_view_context()
    c_context = credito.as_view_context()
    contramov = Movimiento.tomar(id=credito.id_contramov)
    cm_context = contramov.as_view_context()
    assert e_context.get('es_automatico') is not None
    assert not e_context['es_automatico']
    assert not c_context['es_automatico']
    assert cm_context['es_automatico']
