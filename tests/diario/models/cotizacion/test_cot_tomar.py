import pytest
from django.core.exceptions import EmptyResultSet

from diario.models import Cotizacion


def test_devuelve_cotizacion_de_una_moneda_en_una_fecha(
        cotizacion_dolar, cotizacion_posterior_dolar, dolar, fecha_posterior):
    assert Cotizacion.tomar(moneda=dolar, fecha=fecha_posterior) == cotizacion_posterior_dolar


def test_si_no_encuentra_cotizacion_de_moneda_en_fecha_devuelve_ultima_cotizacion_anterior(
        cotizacion_dolar, cotizacion_posterior_dolar, dolar, fecha_tardia):
    assert Cotizacion.tomar(moneda=dolar, fecha=fecha_tardia) == cotizacion_posterior_dolar


def test_si_no_encuentra_ninguna_cotizacion_de_moneda_da_error(peso, fecha):
    Cotizacion.tomar(moneda=peso, fecha=fecha).delete()
    with pytest.raises(EmptyResultSet):
        Cotizacion.tomar(moneda=peso, fecha=fecha)


def test_toma_fecha_de_hoy_por_defecto(cotizacion_dolar, dolar, mock_today):
    hoy = mock_today.return_value
    cotizacion_actual = Cotizacion.crear(moneda=dolar, fecha=hoy, importe_compra=255, importe_venta=275)
    assert Cotizacion.tomar(moneda=dolar) == cotizacion_actual


def test_si_no_recibe_moneda_da_error(cotizacion_dolar, fecha):
    with pytest.raises(TypeError):
        Cotizacion.tomar(fecha=fecha)


def test_si_recibe_argumento_distinto_a_fecha_o_moneda_da_error(
        cotizacion_dolar, cotizacion_posterior_dolar, dolar, fecha):
    with pytest.raises(TypeError):
        Cotizacion.tomar(moneda=dolar, importe_compra=cotizacion_dolar.importe_compra)
