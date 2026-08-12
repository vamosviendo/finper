from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import Cotizacion


def test_hace_una_sola_query_a_cotizacion(dolar, euro, fecha):
    Cotizacion.crear(moneda=dolar, fecha=fecha, importe_compra=10, importe_venta=11)
    Cotizacion.crear(moneda=euro, fecha=fecha, importe_compra=20, importe_venta=21)

    with CaptureQueriesContext(connection) as ctx:
        Cotizacion.precargar([dolar, euro], fecha)

    queries = sum(1 for q in ctx.captured_queries if "diario_cotizacion" in q["sql"])
    assert queries == 1
