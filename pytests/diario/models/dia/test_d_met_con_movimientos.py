from django.db.models import QuerySet

from diario.models import Dia


def test_devuelve_queryset_con_dias_con_movimientos(entrada, entrada_anterior, salida_posterior, dia_tardio):
    result = Dia.con_movimientos()
    assert type(result) is QuerySet
    for dia in [x.dia for x in [entrada, entrada_anterior, salida_posterior]]:
        assert dia in result
    assert dia_tardio not in result


def test_devuelve_dias_ordenados_por_fecha(entrada, entrada_anterior, salida_posterior):
    for dia in Dia.con_movimientos():
        print(dia)
    for dia in [entrada_anterior.dia, entrada.dia, salida_posterior.dia]:
        print(dia)
    assert list(Dia.con_movimientos()) == [entrada_anterior.dia, entrada.dia, salida_posterior.dia]
