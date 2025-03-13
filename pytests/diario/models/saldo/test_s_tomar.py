import pytest

from diario.models import Saldo, Movimiento


def test_si_no_encuentra_saldo_de_cuenta_en_movimiento_busca_ultimo_saldo_anterior(
        entrada_otra_cuenta, cuenta_2, salida_posterior):
    assert \
        Saldo.tomar(cuenta=cuenta_2, movimiento=salida_posterior) == \
        Saldo.objects.get(cuenta=cuenta_2, movimiento=entrada_otra_cuenta)


def test_busca_saldo_anterior_por_fecha_y_orden_dia(
        entrada_posterior_otra_cuenta, entrada_otra_cuenta, cuenta_2, entrada_tardia):

    assert \
        Saldo.tomar(cuenta=cuenta_2, movimiento=entrada_tardia) == \
        Saldo.objects.get(
            cuenta=cuenta_2,
            movimiento=entrada_posterior_otra_cuenta
        )


def test_si_no_encuentra_saldo_de_cuenta_en_movimiento_ni_saldos_anteriores_lanza_excepcion(
        entrada, cuenta_2):
    with pytest.raises(Saldo.DoesNotExist):
        Saldo.tomar(cuenta=cuenta_2, movimiento=entrada)


def test_si_cuenta_es_acumulativa_y_movimiento_es_de_fecha_posterior_a_su_conversion_devuelve_saldo_cuyo_importe_es_suma_de_importes_de_saldos_de_subcuentas_al_momento_del_movimiento(
        cuenta, fecha_posterior):
    sc1, sc2 = cuenta.dividir_entre(
        ['subcuenta 1', 'sc1', 0],
        ['subcuenta 2', 'sc2'],
        fecha=cuenta.fecha_creacion
    )
    Movimiento.crear('mov', 50, sc1, fecha=fecha_posterior)
    mov = Movimiento.crear('mov2', 20, None, sc2, fecha=fecha_posterior)
    cuenta = cuenta.tomar_del_slug()

    assert Saldo.tomar(cuenta=cuenta, movimiento=mov).importe == sc1.saldo(mov) + sc2.saldo(mov)


def test_si_cuenta_es_acumulativa_y_movimiento_es_de_fecha_anterior_a_su_conversion_devuelve_saldo_original_en_movimiento(
        cuenta, entrada, fecha_posterior):
    saldo_en_entrada = cuenta.saldo(entrada)
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', 0],
        ['subcuenta 2', 'sc2'],
        fecha=fecha_posterior
    )
    assert Saldo.tomar(cuenta=cuenta, movimiento=entrada).importe == saldo_en_entrada


def test_si_cuenta_es_acumulativa_y_movimiento_es_de_la_misma_fecha_que_su_conversion_con_traspaso_de_saldo_devuelve_saldo_original_si_movimiento_es_anterior_a_conversion(
        cuenta, entrada, fecha_posterior):
    mov = Movimiento.crear('mov2', 20, None, cuenta, fecha=fecha_posterior)
    saldo_en_mov = cuenta.saldo(mov)
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', 20],
        ['subcuenta 2', 'sc2'],
        fecha=fecha_posterior
    )
    assert Saldo.tomar(cuenta=cuenta, movimiento=mov).importe == saldo_en_mov


def test_si_cuenta_es_acumulativa_y_movimiento_es_de_la_misma_fecha_que_su_conversion_con_traspaso_de_saldo_devuelve_suma_de_importes_de_saldos_de_subcuentas_si_movimiento_es_posterior_a_conversion(
        cuenta, fecha_posterior):
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', 20],
        ['subcuenta 2', 'sc2'],
        fecha=fecha_posterior
    )
    sc1, sc2 = cuenta.subcuentas.all()
    mov = Movimiento.crear('mov2', 20, None, sc1, fecha=fecha_posterior)
    assert Saldo.tomar(cuenta=cuenta, movimiento=mov).importe == sc1.saldo(mov) + sc2.saldo(mov)


def test_si_cuenta_es_acumulativa_y_movimiento_es_de_la_misma_fecha_que_su_conversion_sin_traspaso_de_saldo_devuelve_saldo_original_si_movimiento_es_anterior_a_conversion(
        cuenta, entrada, fecha_posterior):
    mov = Movimiento.crear('mov2', 20, None, cuenta, fecha=fecha_posterior)
    saldo_en_mov = cuenta.saldo(mov)
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', 0],
        ['subcuenta 2', 'sc2'],
        fecha=fecha_posterior
    )
    assert Saldo.tomar(cuenta=cuenta, movimiento=mov).importe == saldo_en_mov


def test_si_cuenta_es_acumulativa_y_movimiento_es_de_la_misma_fecha_que_su_conversion_sin_traspaso_de_saldo_devuelve_suma_de_importes_de_saldos_de_subcuentas_si_movimiento_es_posterior_a_conversion(
        cuenta, entrada, fecha_posterior):
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', 0],
        ['subcuenta 2', 'sc2'],
        fecha=fecha_posterior
    )
    sc1, sc2 = cuenta.subcuentas.all()
    mov = Movimiento.crear('mov2', 20, None, sc1, fecha=fecha_posterior)
    assert Saldo.tomar(cuenta=cuenta, movimiento=mov).importe == sc1.saldo(mov) + sc2.saldo(mov)


def test_si_cuenta_es_acumulativa_y_no_tiene_movs_directos_y_movimiento_es_de_la_misma_fecha_que_su_conversion_devuelve_suma_de_importes_de_saldos_de_subcuentas_si_movimiento_es_posterior_a_conversion(
        cuenta, fecha_posterior):
    cuenta = cuenta.dividir_y_actualizar(
        ['subcuenta 1', 'sc1', 0],
        ['subcuenta 2', 'sc2'],
        fecha=fecha_posterior
    )
    sc1, sc2 = cuenta.subcuentas.all()
    mov = Movimiento.crear('mov2', 20, None, sc1, fecha=fecha_posterior)
    assert Saldo.tomar(cuenta=cuenta, movimiento=mov).importe == sc1.saldo(mov) + sc2.saldo(mov)
