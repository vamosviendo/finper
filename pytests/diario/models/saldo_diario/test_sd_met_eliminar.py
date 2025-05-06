import pytest

from diario.models import SaldoDiario


def test_elimina_saldo(saldo_diario):
    saldo_diario.eliminar()
    assert SaldoDiario.cantidad() == 0

    with pytest.raises(SaldoDiario.DoesNotExist):
        SaldoDiario.objects.get(
            cuenta=saldo_diario.cuenta,
            dia=saldo_diario.dia
        )


def test_modifica_saldos_posteriores_de_la_cuenta(saldo_diario, salida_posterior):
    dia_posterior = salida_posterior.dia
    saldo_posterior = dia_posterior.saldodiario_set.get(cuenta=salida_posterior.cta_salida)
    importe = saldo_diario.importe
    importe_saldo_posterior = saldo_posterior.importe

    saldo_diario.eliminar()
    saldo_posterior.refresh_from_db()

    assert saldo_posterior.importe == importe_saldo_posterior - importe


def test_no_modifica_saldos_posteriores_de_otra_cuenta(saldo_diario, entrada_posterior_otra_cuenta):
    dia_posterior = entrada_posterior_otra_cuenta.dia
    saldo_posterior_otra_cuenta = dia_posterior.saldodiario_set.get(cuenta=entrada_posterior_otra_cuenta.cta_entrada)
    importe_saldo_posterior = saldo_posterior_otra_cuenta.importe

    saldo_diario.eliminar()
    saldo_posterior_otra_cuenta.refresh_from_db()

    assert saldo_posterior_otra_cuenta.importe == importe_saldo_posterior

#
#
# def test_llama_a_recalcular_saldos_de_cuenta_de_saldo_eliminado_desde_fecha_de_saldo_en_adelante(
#         saldo, salida_posterior, mocker):
#     mock_recalcular = mocker.patch('diario.models.Cuenta.recalcular_saldos_entre', autospec=True)
#     saldo.eliminar()
#     mock_recalcular.assert_called_once_with(saldo.cuenta, saldo.posicion)
