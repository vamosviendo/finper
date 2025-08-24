import pytest
from django.core.exceptions import ValidationError

from diario.models import Cotizacion


def test_se_relaciona_con_una_moneda(dolar, fecha_posterior):
    cotizacion = Cotizacion.crear(
        moneda=dolar,
        fecha=fecha_posterior,
        importe_compra=1420,
        importe_venta=1450,
    )
    cotizacion_dolar = dolar.cotizaciones.get(fecha=fecha_posterior)
    assert cotizacion_dolar == cotizacion


def test_se_ordena_por_fecha(
        dolar, euro, peso, fecha_temprana, fecha_inicial, cotizacion_tardia_dolar, cotizacion_dolar, cotizacion_posterior_dolar):
    cotizacion_temprana_dolar = dolar.cotizaciones.get(fecha=fecha_temprana)
    cotizacion_temprana_euro = euro.cotizaciones.get(fecha=fecha_temprana)
    cotizacion_peso = peso.cotizaciones.get(fecha=fecha_inicial)
    assert list(Cotizacion.todes()) == [
        cotizacion_peso,
        cotizacion_temprana_dolar,
        cotizacion_temprana_euro,
        cotizacion_dolar,
        cotizacion_posterior_dolar,
        cotizacion_tardia_dolar
    ]


def test_solo_puede_haber_una_por_fecha_por_moneda(dolar, cotizacion_dolar):
    cotizacion_2 = Cotizacion(moneda=dolar, fecha=cotizacion_dolar.fecha, importe_compra=1532, importe_venta=1561)
    with pytest.raises(ValidationError):
        cotizacion_2.full_clean()


def test_permite_cotizaciones_de_igual_fecha_para_monedas_distintas(dolar, euro, cotizacion_dolar):
    cotizacion_2 = Cotizacion(moneda=euro, fecha=cotizacion_dolar.fecha, importe_compra=1835, importe_venta=1882)
    try:
        cotizacion_2.full_clean()   # No debe dar ValidationError
    except ValidationError:
        pytest.fail("No permite cotizaciones de monedas distintas en la misma fecha")

def test_str_devuelve_moneda_fecha_e_importe_de_cotizacion(cotizacion_dolar):
    assert \
        str(cotizacion_dolar) == \
        f"Cotización {cotizacion_dolar.moneda} al {cotizacion_dolar.fecha}: " \
        f"{cotizacion_dolar.importe_compra} / {cotizacion_dolar.importe_venta}"
