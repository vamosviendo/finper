from django.db import connection, models
from django.test.utils import CaptureQueriesContext


def test_devuelve_solo_cuentas_interactivas_del_titular(titular, cuenta, cuenta_2):
    resultado = titular.cuentas_interactivas()
    assert isinstance(resultado, models.QuerySet)
    assert set(resultado) == {cuenta, cuenta_2}


def test_excluye_cuentas_de_otros_titulares(titular, otro_titular, cuenta, cuenta_ajena):
    assert cuenta_ajena not in titular.cuentas_interactivas()


def test_hace_no_mas_que_3_queries(titular, cuenta, cuenta_2):
    with CaptureQueriesContext(connection) as ctx:
        list(titular.cuentas_interactivas())

    queries = sum(1 for q in ctx.captured_queries if "diario_cuenta" in q["sql"])
    assert queries <= 3
