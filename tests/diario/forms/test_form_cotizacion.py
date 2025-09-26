import warnings

import pytest

from diario.forms import FormCotizacion
from diario.models import Cotizacion


@pytest.fixture
def formcot(dolar) -> FormCotizacion:
    return FormCotizacion(moneda=dolar)


@pytest.fixture
def formcot_data(fecha) -> dict:
    return {
        "fecha": fecha,
        "importe_compra": 1000,
        "importe_venta": 1050,
    }


@pytest.mark.parametrize("campo", Cotizacion.form_fields)
def test_muestra_campos_necesarios(formcot, campo):
    assert campo in formcot.fields.keys()


def test_debe_recibir_moneda(formcot_data):
    with pytest.warns(UserWarning):
        formcot = FormCotizacion(data=formcot_data)
        assert not formcot.is_valid()


def test_es_valido_con_datos_correctos(dolar, formcot_data):
    formcot = FormCotizacion(data=formcot_data, moneda=dolar)
    assert formcot.is_valid()
    assert formcot.cleaned_data["fecha"] == formcot_data["fecha"]
    assert formcot.cleaned_data["importe_compra"] == formcot_data["importe_compra"]
    assert formcot.cleaned_data["importe_venta"] == formcot_data["importe_venta"]


def test_guarda_correctamente_lo_que_le_corresponde(dolar, formcot_data):
    formcot = FormCotizacion(data=formcot_data, moneda=dolar)
    assert formcot.is_valid()

    cotizacion = formcot.save(commit=False)

    assert cotizacion.fecha == formcot_data["fecha"]
    assert cotizacion.importe_compra == formcot_data["importe_compra"]
    assert cotizacion.importe_venta == formcot_data["importe_venta"]
    assert cotizacion.moneda_id is None     # moneda es guardada por diario.views.MonCotNuevaView


def test_no_admite_fecha_existente(dolar, cotizacion_dolar, formcot_data):
    formcot_data["fecha"] = cotizacion_dolar.fecha
    formcot = FormCotizacion(data=formcot_data, moneda=dolar)
    assert not formcot.is_valid()


def test_si_esta_atado_a_instancia_toma_moneda_de_la_instancia(cotizacion_dolar):
    formcot = FormCotizacion(instance=cotizacion_dolar)
    assert formcot.moneda == cotizacion_dolar.moneda
