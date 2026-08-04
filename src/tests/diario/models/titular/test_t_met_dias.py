from django.db import connection
from django.db.models import QuerySet
from django.test.utils import CaptureQueriesContext

from diario.models import Movimiento


def _contar(queries, tabla):
    return sum(1 for q in queries if tabla in q["sql"])


def test_devuelve_queryset_con_dias_con_movimientos_de_cuentas_del_titular(
        titular, dia, dia_posterior, dia_tardio,
        entrada, salida, entrada_posterior_cuenta_ajena, salida_tardia_tercera_cuenta):
    dias_titular = titular.dias()
    assert isinstance(dias_titular, QuerySet)
    assert list(titular.dias()) == [dia, dia_tardio]


def test_titular_dias_hace_maximo_2_queries(titular, cuenta, entrada, salida_posterior):
    """ Titular.dias debe hacer 2 queries:
        una a diario_movimiento y otra a diario_dia """
    with CaptureQueriesContext(connection) as ctx:
        list(titular.dias())

    assert _contar(ctx.captured_queries, 'diario_movimiento') == 1
    assert _contar(ctx.captured_queries, 'diario_dia') == 1


def test_titular_dias_hace_maximo_2_queries_con_cuentas_en_ambas_tablas(
        otro_titular, cuenta, cuenta_de_dos_titulares, dia, dia_posterior):
    """Aunque titular.cuentas y titular.ex_cuentas sean dos related_managers,
    las queries se resuelven internamente sin queries adicionales."""
    sc1 = cuenta_de_dos_titulares.subcuentas.first()
    Movimiento.crear("movimiento", 100, sc1, dia=dia)
    Movimiento.crear("movimiento posterior", 150, sc1, dia=dia_posterior)

    with CaptureQueriesContext(connection) as ctx:
        list(otro_titular.dias())

    assert _contar(ctx.captured_queries, 'diario_movimiento') == 1
    assert _contar(ctx.captured_queries, 'diario_dia') == 1
