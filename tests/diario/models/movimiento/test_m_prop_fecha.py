from diario.models import Dia


def test_devuelve_fecha_del_dia_del_movimiento(entrada):
    assert entrada.fecha == entrada.dia.fecha


def test_setea_campo_dia_al_dia_de_la_fecha_dada(entrada, dia_posterior):
    entrada.fecha = dia_posterior.fecha
    assert entrada.dia == dia_posterior


def test_si_no_existe_dia_de_la_fecha_dada_lo_crea(entrada, fecha_posterior):
    entrada.fecha = fecha_posterior
    dia_posterior = Dia.tomar(fecha=fecha_posterior)
    assert entrada.dia == dia_posterior
