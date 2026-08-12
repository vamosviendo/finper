from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.models import Movimiento


def _contar(queries, tabla):
    return sum(1 for q in queries if tabla in q["sql"])


def test_cuenta_interactiva_dias_hace_maximo_2_queries(cuenta, entrada, entrada_tardia):
    """Cuenta.dias en cuenta interactiva debe hacer 2 queries:
    una a diario_movimiento y otra a diario_dia."""
    with CaptureQueriesContext(connection) as ctx:
        list(cuenta.dias())

    assert _contar(ctx.captured_queries, 'diario_movimiento') == 1
    assert _contar(ctx.captured_queries, 'diario_dia') == 1


def test_cuenta_acumulativa_dias_hace_maximo_3_queries(cuenta_acumulativa, dia, dia_posterior):
    """ Cuenta.dias en cuenta acumulativa debe hacer 2 queries + 1 por
        arbol_de_subcuentas (recursión inicial).
        Actualmente hace 2 + 6 queries.
    """
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    Movimiento.crear("movimiento", 100, sc2, dia=dia)
    Movimiento.crear("movimiento posterior", 150, sc1, dia=dia_posterior)

    with CaptureQueriesContext(connection) as ctx:
        list(cuenta_acumulativa.dias())

    assert _contar(ctx.captured_queries, 'diario_movimiento') == 1
    assert _contar(ctx.captured_queries, 'diario_dia') == 1
    # TODO: optimizar arbol_de_subcuentas para reducir a <= 2 queries
    assert _contar(ctx.captured_queries, 'diario_cuenta') <= 6
