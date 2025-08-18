from diario.models import Dia


def test_devuelve_fecha_del_ultimo_dia_con_movimientos(entrada, salida_posterior, dia_tardio):
    assert Dia.ultima_fecha_con_movimientos() == salida_posterior.dia.fecha
