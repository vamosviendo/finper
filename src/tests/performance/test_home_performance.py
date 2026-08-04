import time

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse


def contar(queries, tabla):
    return sum(1 for q in queries if tabla in q["sql"])


@pytest.mark.slow
def test_home_queries_por_tabla_no_explota(client, bd_escalable):
    """Las queries a tablas críticas deben ser O(1) u O(pequeño)"""
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(reverse("home"))

    assert response.status_code == 200

    # Asserts laxos por tabla. Si fallan, hay N+1
    assert contar(ctx, "diario_movimiento") < 50
    assert contar(ctx, "diario_saldodiario") < 50
    assert contar(ctx, "diario_cotizacion") < 20
    assert contar(ctx, "diario_cuenta") < 20
    assert contar(ctx, "diario_titular") < 20


@pytest.mark.slow
def test_home_tiempo_total_en_bd_mediana(client, bd_mediana):
    inicio = time.perf_counter()
    client.get(reverse("home"))
    tiempo = time.perf_counter() - inicio
    assert tiempo < 2.0, f"Tiempo {tiempo:.3f}s excede 2000 ms"


@pytest.mark.slow
@pytest.mark.nomonbase
def test_home_bd_completa_smoke(client, bd_completa):
    with CaptureQueriesContext(connection) as ctx:
        inicio = time.perf_counter()
        response = client.get(reverse("home"))
        tiempo = time.perf_counter() - inicio
    assert response.status_code == 200
    assert tiempo < 3.0, f"Tiempo {tiempo:.0f}ms, baseline 6500-7500ms"
    print(f"Tiempo: {tiempo}")
    assert len(ctx.captured_queries) < 1500, (
        f"Queries {len(ctx.captured_queries)}, baseline 3353"
    )
