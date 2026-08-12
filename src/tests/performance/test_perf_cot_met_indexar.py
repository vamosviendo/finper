from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import Cotizacion


def test_hace_maximo_una_query_a_cotizacion(
        cuenta, cuenta_en_dolares, peso, dolar, fecha):
    Cotizacion.crear(moneda=peso, fecha=fecha, importe_compra=1, importe_venta=1)
    Cotizacion.crear(moneda=dolar, fecha=fecha, importe_compra=100, importe_venta=110)

    with CaptureQueriesContext(connection) as ctx:
        Cotizacion.indexar([cuenta, cuenta_en_dolares], [peso, dolar], fecha)

    queries = sum(1 for q in ctx.captured_queries if "diario_cotizacion" in q["sql"])
    assert queries <= 1
