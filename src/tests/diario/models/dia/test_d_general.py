import pytest
from django.core.exceptions import ValidationError

from diario.models import Dia


def test_guarda_y_recupera_dias(fecha):
    dia = Dia()
    dia.fecha = fecha
    dia.sk = fecha.strftime("%Y%m%d")
    dia.clean_save()

    assert Dia.cantidad() == 1
    Dia.tomar(fecha=fecha)     # No da error


def test_no_permite_fechas_duplicadas(dia):
    dia2 = Dia(fecha=dia.fecha)
    with pytest.raises(ValidationError):
        dia2.full_clean()


def test_se_ordena_por_fecha_ascendente(fecha, fecha_posterior, fecha_tardia):
    dia_tardio = Dia.crear(fecha=fecha_tardia)
    dia_posterior = Dia.crear(fecha=fecha_posterior)
    dia = Dia.crear(fecha=fecha)

    assert list(Dia.todes()) == [dia, dia_posterior, dia_tardio]


def test_no_permite_dias_sin_fecha(fecha):
    dia = Dia(sk=fecha.strftime("%Y%m%d"))
    with pytest.raises(ValidationError):
        dia.full_clean()


def test_natural_key_devuelve_fecha(dia):
    assert dia.natural_key() == (dia.fecha, )


def test_genera_sk_a_partir_de_fecha(fecha):
    dia = Dia(fecha=fecha)
    dia.clean_save()
    assert dia.sk == fecha.strftime("%Y%m%d")


def test_no_permite_sk_duplicada(dia, fecha_posterior):
    dia = Dia(fecha=fecha_posterior, sk=dia.sk)
    with pytest.raises(ValidationError):
        dia.full_clean()
