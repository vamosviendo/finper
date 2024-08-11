from django.db.models import QuerySet

from diario.models import Movimiento


def test_devuelve_queryset_con_movimientos(dia):
    assert isinstance(dia.movimientos_filtrados(), QuerySet)


def test_si_no_recibe_argumentos_devuelve_queryset_con_todos_los_movimientos_del_dia(
        dia, entrada, entrada_otra_cuenta, salida_posterior, entrada_posterior_otra_cuenta):
    assert list(dia.movimientos_filtrados()) == [entrada, entrada_otra_cuenta]


def test_si_recibe_cuenta_devuelve_solo_los_movimientos_del_dia_en_los_que_interviene_la_cuenta(
        dia, cuenta, entrada, salida, entrada_otra_cuenta, salida_posterior, entrada_posterior_otra_cuenta):
    assert list(dia.movimientos_filtrados(cuenta=cuenta)) == [entrada, salida]


def test_si_recibe_cuenta_acumulativa_devuelve_movimientos_del_dia_en_los_que_interviene_la_cuenta_o_sus_subcuentas(
        dia, dia_posterior, cuenta):
    sc11, sc12 = cuenta.dividir_entre(
        {'nombre': 'subcuenta 1', 'slug': 'sc1', 'saldo': 30, },
        {'nombre': 'subcuenta 2', 'slug': 'sc2', },
        fecha=dia.fecha
    )
    cuenta = cuenta.tomar_del_slug()
    mov_subcuenta = Movimiento.crear(
        concepto='movsubc', importe=10, cta_salida=sc11, dia=dia)
    mov_subcuenta_2 = Movimiento.crear(
        concepto='movsubc2', importe=25, cta_entrada=sc12, dia=dia_posterior
    )
    assert mov_subcuenta in dia.movimientos_filtrados(cuenta)
    assert mov_subcuenta_2 not in dia.movimientos_filtrados(cuenta)


def test_si_recibe_titular_devuelve_solo_los_movimientos_del_dia_en_los_que_intervienen_cuentas_del_titular(
        dia, titular, entrada, salida, entrada_cuenta_ajena):
    assert list(dia.movimientos_filtrados(titular=titular)) == [entrada, salida]


def test_si_recibe_cuenta_y_titular_no_toma_en_cuenta_el_argumento_titular(
        dia, cuenta_ajena, titular, entrada, salida, entrada_cuenta_ajena):
    assert list(dia.movimientos_filtrados(cuenta=cuenta_ajena, titular=titular)) == [entrada_cuenta_ajena]
