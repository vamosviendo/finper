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


def test_si_cuenta_es_acumulativa_devuelve_saldo_cuyo_importe_es_suma_de_importes_de_saldos_de_subcuentas_al_momento_del_movimiento(
        cuenta, fecha_posterior):
    sc1, sc2 = cuenta.dividir_entre(
        ['subcuenta 1', 'sc1', 0],
        ['subcuenta 2', 'sc2'],
        fecha=cuenta.fecha_creacion
    )
    Movimiento.crear('mov', 50, sc1, fecha=fecha_posterior)
    mov = Movimiento.crear('mov2', 20, None, sc2, fecha=fecha_posterior)
    cuenta = cuenta.tomar_del_slug()

    assert Saldo.tomar(cuenta=cuenta, movimiento=mov).importe == 50 - 20
