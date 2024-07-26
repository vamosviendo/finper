def test_incluye_la_fecha_del_dia(dia):
    assert dia.as_view_context().get("fecha") is not None
    assert dia.as_view_context()["fecha"] == dia.fecha


def test_incluye_movimientos_del_dia(dia, entrada, salida, entrada_otra_cuenta, salida_posterior):
    context = dia.as_view_context()
    assert context.get("movimientos") is not None
    assert context["movimientos"] == [entrada, salida, entrada_otra_cuenta]


def test_si_recibe_cuenta_incluye_solo_movimientos_de_la_cuenta(
        dia, cuenta, entrada, salida, entrada_otra_cuenta, salida_posterior):
    context = dia.as_view_context(cuenta=cuenta)
    assert context["movimientos"] == [entrada, salida]
