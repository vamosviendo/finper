from django.core.exceptions import FieldError

from diario.models import Movimiento, Dia


def test_filtra_por_dia(entrada, salida, entrada_anterior, salida_posterior):
    assert set(Movimiento.filtro(dia=Dia.tomar(fecha=entrada.fecha))) == {entrada, salida}


def test_permite_filtrar_movimientos_por_fecha(entrada, salida, entrada_anterior, salida_posterior):
    try:
        queryset = Movimiento.filtro(fecha=entrada.fecha)
    except FieldError:
        raise AssertionError("No permite filtrar movimientos por fecha.")

    assert set(queryset) == {entrada, salida}
