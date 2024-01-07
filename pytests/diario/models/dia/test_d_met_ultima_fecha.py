from diario.models import Dia


def test_devuelve_fecha_del_ultimo_movimiento(dia, dia_posterior, dia_tardio):
    assert Dia.ultima_fecha() == dia_tardio.fecha
