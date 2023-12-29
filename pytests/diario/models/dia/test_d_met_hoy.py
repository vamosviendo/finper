from datetime import date

from diario.models import Dia


def test_devuelve_dia_con_fecha_de_hoy(dia_hoy):
    assert Dia.hoy().fecha == date.today()


def test_si_no_existe_dia_con_fecha_de_hoy_lo_crea():
    assert Dia.hoy().fecha == date.today()