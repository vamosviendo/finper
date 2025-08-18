from django.db.models import QuerySet


def test_devuelve_queryset_con_dias_con_movimientos_de_cuentas_del_titular(
        titular, dia, dia_posterior, dia_tardio,
        entrada, salida, entrada_posterior_cuenta_ajena, salida_tardia_tercera_cuenta):
    dias_titular = titular.dias()
    assert isinstance(dias_titular, QuerySet)
    assert list(titular.dias()) == [dia, dia_tardio]