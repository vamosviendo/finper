import pytest

from diario.models import Saldo


def test_elimina_saldo(saldo):
    saldo.eliminar()
    assert Saldo.cantidad() == 0

    with pytest.raises(Saldo.DoesNotExist):
        Saldo.objects.get(
            cuenta=saldo.cuenta,
            movimiento=saldo.movimiento
        )


def test_modifica_saldos_posteriores(saldo, salida_posterior):
    saldo_posterior = salida_posterior.saldo_set.first()
    importe_saldo_posterior = saldo_posterior.importe

    saldo.eliminar()
    saldo_posterior.refresh_from_db()

    assert saldo_posterior.importe == importe_saldo_posterior - saldo.importe


def test_llama_a_recalcular_saldos_de_cuenta_de_saldo_eliminado_desde_fecha_de_saldo_en_adelante(
        saldo, salida_posterior, mocker):
    mock_recalcular = mocker.patch('diario.models.Cuenta.recalcular_saldos_entre', autospec=True)
    saldo.eliminar()
    mock_recalcular.assert_called_once_with(saldo.cuenta, saldo.posicion)
