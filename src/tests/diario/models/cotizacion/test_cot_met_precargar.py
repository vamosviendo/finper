from datetime import date, timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import Cotizacion


def test_devuelve_dict_con_ultima_cotizacion_hasta_fecha_para_cada_moneda(dolar, euro, fecha):
    Cotizacion.crear(moneda=dolar, fecha=fecha, importe_compra=10, importe_venta=11)
    Cotizacion.crear(moneda=euro, fecha=fecha, importe_compra=20, importe_venta=21)

    resultado = Cotizacion.precargar([dolar, euro], fecha)

    assert type(resultado) is dict
    assert resultado[dolar.pk]["compra"] == 10
    assert resultado[dolar.pk]["venta"] == 11
    assert resultado[euro.pk]["compra"] == 20
    assert resultado[euro.pk]["venta"] == 21


def test_toma_la_cotizacion_mas_reciente_anterior_a_fecha(dolar, fecha, fecha_anterior):
    Cotizacion.crear(
        moneda=dolar, fecha=fecha_anterior,
        importe_compra=5, importe_venta=6
    )
    Cotizacion.crear(
        moneda=dolar, fecha=fecha,
        importe_compra=10, importe_venta=11
    )

    resultado = Cotizacion.precargar([dolar], fecha + timedelta(1))

    assert resultado[dolar.pk]["compra"] == 10
    assert resultado[dolar.pk]["venta"] == 11
    assert resultado[dolar.pk]["fecha"] == fecha


def test_devuelve_dict_vacio_si_no_hay_cotizaciones(dolar, fecha):
    for cotizacion in dolar.cotizaciones.all():
        cotizacion.delete()
    resultado = Cotizacion.precargar([dolar], fecha)
    assert resultado == {}


def test_hace_una_sola_query_a_cotizacion(dolar, euro, fecha):
    Cotizacion.crear(moneda=dolar, fecha=fecha, importe_compra=10, importe_venta=11)
    Cotizacion.crear(moneda=euro, fecha=fecha, importe_compra=20, importe_venta=21)

    with CaptureQueriesContext(connection) as ctx:
        Cotizacion.precargar([dolar, euro], fecha)

    queries = sum(1 for q in ctx.captured_queries if "diario_cotizacion" in q["sql"])
    assert queries == 1
