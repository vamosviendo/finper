import pytest


@pytest.fixture
def context(dia):
    return dia.as_view_context()

def test_incluye_la_fecha_del_dia(dia, context):
    assert context.get("fecha") is not None
    assert context["fecha"] == dia.fecha


def test_incluye_movimientos_del_dia(dia, entrada, salida, entrada_otra_cuenta, salida_posterior, context):
    assert context.get("movimientos") is not None
    assert context["movimientos"] == [entrada, salida, entrada_otra_cuenta]


def test_incluye_representacion_del_dia_incluyendo_dia_de_la_semana(dia, context):
    assert context.get("str_dia_semana") is not None
    assert context["str_dia_semana"] == dia.str_dia_semana()


def test_incluye_saldo_del_dia(dia, entrada, context):
    assert context.get("saldo") is not None
    assert context["saldo"] == dia.saldo()


def test_si_recibe_cuenta_incluye_solo_movimientos_de_la_cuenta(
        dia, cuenta, entrada, salida, entrada_otra_cuenta, salida_posterior):
    context = dia.as_view_context(cuenta=cuenta)
    assert context["movimientos"] == [entrada, salida]


def test_si_recibe_titular_incluye_solo_movimientos_del_titular(
        dia, titular, entrada, salida, entrada_otra_cuenta, entrada_cuenta_ajena):
    context = dia.as_view_context(titular=titular)
    assert context["movimientos"] == [entrada, salida, entrada_otra_cuenta]


def test_si_recibe_cuenta_y_titular_solo_toma_en_cuenta_la_cuenta_valga_la_redundancia(
        dia, cuenta_ajena, titular, entrada, salida, entrada_cuenta_ajena):
    context = dia.as_view_context(cuenta=cuenta_ajena, titular=titular)
    assert context["movimientos"] == [entrada_cuenta_ajena]
