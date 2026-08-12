from django.db import connection
from django.test.utils import CaptureQueriesContext


def test_hace_no_mas_que_3_queries(titular, cuenta, cuenta_2):
    with CaptureQueriesContext(connection) as ctx:
        list(titular.cuentas_interactivas())

    queries = sum(1 for q in ctx.captured_queries if "diario_cuenta" in q["sql"])
    assert queries <= 3
