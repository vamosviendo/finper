from datetime import timedelta

import pytest

from diario.models import Dia


def test_add_toma_dia_con_n_dias_posteriores_a_la_fecha(dia):
    dia1 = Dia.crear(fecha=dia.fecha+timedelta(1))
    dia5 = Dia.crear(fecha=dia.fecha+timedelta(5))
    assert dia.timedelta(1) == dia1
    assert dia.timedelta(5) == dia5

def test_add_crea_dia_con_n_dias_posteriores_a_la_fecha(dia):
    with pytest.raises(Dia.DoesNotExist):
        Dia.tomar(fecha=dia.fecha+timedelta(1))
    assert dia.timedelta(1) == Dia.tomar(fecha=dia.fecha+timedelta(1))
    with pytest.raises(Dia.DoesNotExist):
        Dia.tomar(fecha=dia.fecha+timedelta(5))
    assert dia.timedelta(5) == Dia.tomar(fecha=dia.fecha+timedelta(5))
