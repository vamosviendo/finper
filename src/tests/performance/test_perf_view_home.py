import time

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse


def contar(queries, tabla):
    return sum(1 for q in queries if tabla in q["sql"])


@pytest.mark.slow
@pytest.mark.parametrize(
    "bd_escalable, limites", [
        ("chico", {"mov": 50, "saldo": 50, "cot": 10, "cta": 150, "tit": 10}),
        ("mediano", {"mov": 100, "saldo": 100, "cot": 10, "cta": 250, "tit": 15}),
        ("grande", {"mov": 150, "saldo": 150, "cot": 10, "cta": 350, "tit": 20})
    ],
    indirect=["bd_escalable"],
)
def test_home_queries_por_tabla_no_explota(client, bd_escalable, limites):
    """Las queries a tablas críticas deben ser O(1) u O(pequeño)"""
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(reverse("home"))

    assert response.status_code == 200

    # Asserts laxos por tabla. Si fallan, hay N+1
    assert contar(ctx, "diario_movimiento") < limites["mov"]
    assert contar(ctx, "diario_saldodiario") < limites["saldo"]
    assert contar(ctx, "diario_cotizacion") < limites["cot"]
    assert contar(ctx, "diario_cuenta") < limites["cta"]
    assert contar(ctx, "diario_titular") < limites["tit"]


@pytest.mark.slow
@pytest.mark.nomonbase
def test_home_bd_completa_smoke(client, bd_completa):
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(reverse("home"))
    assert response.status_code == 200
    # assert tiempo < 3.0, f"Tiempo {tiempo:.0f}ms, baseline 6500-7500ms"

    assert len(ctx.captured_queries) < 1800, (
        f"Queries {len(ctx.captured_queries)}, baseline 3353"
    )

# @pytest.mark.xfail
@pytest.mark.slow
def test_home_usa_batch_de_cotizaciones(client, bd_mediana):
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(reverse("home"))

    queries = sum(
        1 for q in ctx.captured_queries if "diario_cotizacion" in q["sql"]
    )
    assert queries <= 3, f"Hizo {queries} queries a cotizacion (más de las 3 esperadas)"
