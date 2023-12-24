import pytest
from django.core.exceptions import ValidationError

from diario.models import Dia


def test_guarda_y_recupera_dias(fecha):
    dia = Dia()
    dia.fecha = fecha
    dia.full_clean()
    dia.save()

    assert Dia.cantidad() == 1
    dia = Dia.tomar(fecha=fecha)     # No da error


def test_no_permite_fechas_duplicadas(dia):
    dia2 = Dia(fecha=dia.fecha)
    with pytest.raises(ValidationError):
        dia2.full_clean()
