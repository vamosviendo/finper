from django.db import connection
from django.test.utils import CaptureQueriesContext

from diario.utils.utils_saldo import saldo_general_historico


def test_usa_batch_de_saldos_con_dia(cuenta, cuenta_2, dia, entrada, entrada_otra_cuenta):
    with CaptureQueriesContext(connection) as ctx:
        saldo_general_historico(dia=dia, cuentas=[cuenta, cuenta_2])

        queries_sd = sum(
            1 for q in ctx.captured_queries if "diario_saldodiario" in q["sql"]
        )
        assert queries_sd <= 2
