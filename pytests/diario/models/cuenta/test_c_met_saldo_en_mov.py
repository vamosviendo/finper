from datetime import timedelta

import pytest

from diario.models import SaldoDiario


def test_devuelve_importe_de_saldo_de_la_cuenta_tomado_al_momento_del_movimiento_dado(
        cuenta, entrada, salida, traspaso, salida_posterior):
    importe_saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=salida.dia).importe
    importe_saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia).importe
    assert cuenta.saldo_en_mov(traspaso) == importe_saldo_diario
    assert cuenta.saldo_en_mov(salida) == importe_saldo_diario - traspaso.importe_cta_entrada
    assert cuenta.saldo_en_mov(entrada) == importe_saldo_diario - traspaso.importe_cta_entrada - salida.importe_cta_salida
    assert cuenta.saldo_en_mov(salida_posterior) == importe_saldo_diario_posterior


def test_si_la_cuenta_no_interviene_en_el_movimiento_devuelve_saldo_en_movimiento_anterior(
        cuenta, entrada, salida, entrada_posterior_otra_cuenta):
    assert cuenta.saldo_en_mov(entrada_posterior_otra_cuenta) == cuenta.saldo_en_mov(salida)


def test_si_la_cuenta_no_interviene_en_el_movimiento_ni_hay_movimientos_anteriores_devuelve_0(
        cuenta_2, entrada, salida, entrada_posterior_otra_cuenta):
    assert cuenta_2.saldo_en_mov(salida) == 0


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_calcula_importe_a_partir_de_saldo_anterior(cuenta, entrada_temprana, entrada_anterior, sentido, request):
    mov = request.getfixturevalue(sentido)
    mov.fecha = entrada_temprana.fecha + timedelta(1)
    mov.clean_save()
    assert \
        cuenta.saldo_en_mov(mov) == \
        cuenta.saldo_en_mov(entrada_temprana) + getattr(mov, f"importe_cta_{sentido}")

def test_x(cuenta, entrada, entrada_anterior, salida_posterior, fecha_temprana):
    print("INICIO TEST")
    saldo_posterior = cuenta.saldo_en_mov(salida_posterior)
    entrada.fecha = fecha_temprana
    print("saldo posterior:", saldo_posterior)
    print("INICIO ACCIÓN")
    entrada.clean_save()

    assert cuenta.saldo_en_mov(salida_posterior) == saldo_posterior
