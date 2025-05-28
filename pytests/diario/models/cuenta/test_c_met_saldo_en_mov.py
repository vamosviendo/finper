from diario.models import SaldoDiario


def test_devuelve_importe_de_saldo_de_la_cuenta_tomado_al_momendo_del_movimiento_dado(
        cuenta, entrada, salida, traspaso, salida_posterior):
    importe_saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=salida.dia).importe
    importe_saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia).importe
    assert cuenta.saldo_en_mov(traspaso) == importe_saldo_diario
    assert cuenta.saldo_en_mov(salida) == importe_saldo_diario - traspaso.importe_cta_entrada
    assert cuenta.saldo_en_mov(entrada) == importe_saldo_diario - traspaso.importe_cta_entrada - salida.importe_cta_salida
    assert cuenta.saldo_en_mov(salida_posterior) == importe_saldo_diario_posterior
