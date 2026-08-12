from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from django.core.management import call_command

from diario.models import Titular, CuentaInteractiva, Cuenta, Dia, Movimiento

PATH_FIXTURE = Path(__file__).resolve().parent.parent.parent.parent / "db_full.json"
FECHA_INICIO = date(2000, 1, 1)

@pytest.fixture(scope="session")
def bd_completa(django_db_setup, django_db_blocker):
    """Carga la base de datos completa desde db_full.json. Skip si no existe."""
    if not PATH_FIXTURE.exists():
        # call_command("serializar_db")
        pytest.skip(
            f"Fixture {PATH_FIXTURE} no encontrada."
            f"Generar con python src/manage.py serializar_db"
        )

    with django_db_blocker.unblock():
        call_command("loaddata", str(PATH_FIXTURE))

# --- Helpers ---

def _crear_titulares_adicionales(cantidad: int) -> list[Titular]:
    return [
        Titular.crear(
            sk=f"perf_tit_{i}",
            nombre=f"Titular perf {i}",
            fecha_alta=FECHA_INICIO
        ) for i in range(cantidad)
    ]

def _crear_cuentas_interactivas(
        cantidad: int, titulares: list[Titular], ) -> list[CuentaInteractiva]:
    cuentas = []
    for i in range(cantidad):
        titular = titulares[i % len(titulares)] if titulares else None
        cuentas.append(
            Cuenta.crear(
                nombre=f"Cuenta perf {i}",
                sk=f"perf_cta_{i}",
                titular=titular,
                fecha_creacion=FECHA_INICIO,
            )
        )
    return cuentas


def _crear_cuenta_acumulativa_con_subcuentas(
        nombre: str,
        sk: str,
        titulares: list[Titular],
        n_subcuentas: int = 3,
) -> list[CuentaInteractiva]:
    madre = Cuenta.crear(
        nombre=nombre,
        sk=sk,
        titular=titulares[0] if titulares else None,
        fecha_creacion=FECHA_INICIO,
    )
    lista_subcuentas = [
        [f"subcuenta {i}", f"sc{i}", 0] for i in range(n_subcuentas)
    ]

    return madre.dividir_entre(*lista_subcuentas, fecha=FECHA_INICIO)


def _crear_dias_con_movimientos(
        cuentas: list[CuentaInteractiva],
        cantidad_dias: int,
        movs_por_dia: int,
        fecha_inicio: date = FECHA_INICIO) -> list[Dia]:
    fecha_inicio += timedelta(days=1)
    dias = []
    for d in range(cantidad_dias):
        dia = Dia.crear(fecha=fecha_inicio + timedelta(days=d))
        dias.append(dia)
        for m in range(movs_por_dia):
            cta = cuentas[(d * movs_por_dia + m) % len(cuentas)]
            Movimiento.crear(
                fecha=dia.fecha,
                concepto=f"mov perf {d}-{m}",
                cta_entrada=cta,
                importe=100,
            )
    return dias


# --- Fixtures ----

@pytest.fixture
def bd_mediana(cuenta, cuenta_2, entrada, salida) -> dict[str, list[Titular | Cuenta]]:
    """ BD mediana para asserts de tiempo absoluto (< 2000 ms) """
    titulares = _crear_titulares_adicionales(4)
    cuentas = _crear_cuentas_interactivas(15, titulares)
    cuentas += _crear_cuenta_acumulativa_con_subcuentas(
        "Madre perf", "perf_mae", titulares, n_subcuentas=3,
    )
    _crear_dias_con_movimientos(cuentas, cantidad_dias=50, movs_por_dia=7)
    return {
        "titulares": titulares,
        "cuentas": cuentas,
    }


@pytest.fixture(
    params=["chico", "mediano", "grande", ]
)
def bd_escalable(request, cuenta, cuenta_2, entrada, salida) -> dict[str, list[int]]:
    """Fixture parametrizable."""
    params_map = {
        "chico":   {"cuentas": 10, "dias": 30, "movs": 200},
        "mediano": {"cuentas": 30, "dias": 100, "movs": 1000},
        "grande":  {"cuentas": 60, "dias": 500, "movs": 2000},
    }
    config = params_map[request.param]
    n_cuentas = config["cuentas"]
    n_dias = config["dias"]
    n_movs = config["movs"]

    titulares = _crear_titulares_adicionales(5)
    cuentas = _crear_cuentas_interactivas(n_cuentas - 3, titulares)
    cuentas += _crear_cuenta_acumulativa_con_subcuentas(
        "Madre perf", "perf_mae", titulares, n_subcuentas=3,
    )
    movs_por_dia = max(1, n_movs // n_dias) if n_dias else 0
    _crear_dias_con_movimientos(
        cuentas,
        cantidad_dias=n_dias,
        movs_por_dia=movs_por_dia,
    )
    return {"param": request.param}
