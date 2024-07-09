import pytest
from django.core.exceptions import ValidationError

from diario.models import Cotizacion


def test_se_relaciona_con_una_moneda(dolar, fecha_posterior):
    cotizacion = Cotizacion.crear(
        moneda=dolar,
        fecha=fecha_posterior,
        importe=1420,
    )
    cotizacion_dolar = dolar.cotizaciones.get(fecha=fecha_posterior)
    assert cotizacion_dolar == cotizacion


def test_se_ordena_por_fecha(dolar, fecha, cotizacion_tardia, cotizacion, cotizacion_posterior):
    cotizacion_en_fecha = dolar.cotizaciones.get(fecha=fecha)
    assert list(Cotizacion.todes()) == [
        cotizacion,
        cotizacion_en_fecha,
        cotizacion_posterior,
        cotizacion_tardia
    ]


def test_solo_puede_haber_una_por_fecha_por_moneda(dolar, cotizacion):
    cotizacion_2 = Cotizacion(moneda=dolar, fecha=cotizacion.fecha, importe=1532)
    with pytest.raises(ValidationError):
        cotizacion_2.full_clean()


def test_permite_cotizaciones_de_igual_fecha_para_monedas_distintas(dolar, euro, cotizacion):
    cotizacion_2 = Cotizacion(moneda=euro, fecha=cotizacion.fecha, importe=1835)
    try:
        cotizacion_2.full_clean()   # No debe dar ValidationError
    except ValidationError:
        pytest.fail("No permite cotizaciones de monedas distintas en la misma fecha")
