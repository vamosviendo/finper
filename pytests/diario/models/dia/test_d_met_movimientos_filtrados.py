from django.db.models import QuerySet


def test_devuelve_queryset_con_movimientos(dia):
    assert isinstance(dia.movimientos_filtrados(), QuerySet)


def test_si_no_recibe_argumentos_devuelve_queryset_contodos_los_movimientos_del_dia(
        dia, entrada, entrada_otra_cuenta, salida_posterior, entrada_posterior_otra_cuenta):
    assert list(dia.movimientos_filtrados()) == [entrada, entrada_otra_cuenta]


def test_si_recibe_cuenta_devuelve_solo_los_movimientos_del_dia_en_los_que_interviene_la_cuenta(
        dia, cuenta, entrada, salida, entrada_otra_cuenta, salida_posterior, entrada_posterior_otra_cuenta):
    assert list(dia.movimientos_filtrados(cuenta=cuenta)) == [entrada, salida]
