from diario.models import Dia


def test_devuelve_id_del_ultimo_dia(dia, dia_posterior, dia_tardio, dia_temprano):
    assert Dia.ultima_id() == dia_tardio.pk
