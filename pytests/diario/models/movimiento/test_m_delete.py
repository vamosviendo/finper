import pytest
from django.core.exceptions import ValidationError

from diario.models import Saldo, Movimiento
from utils import errors


def test_resta_importe_de_saldo_cta_entrada_y_lo_suma_a_saldo_cta_salida(
        entrada, traspaso, cuenta, cuenta_2):
    saldo_cuenta = cuenta.saldo()
    entrada.delete()
    assert cuenta.saldo() == saldo_cuenta - entrada.importe

    saldo_cuenta = cuenta.saldo()
    saldo_cuenta_2 = cuenta_2.saldo()
    traspaso.delete()
    assert cuenta.saldo() == saldo_cuenta - traspaso.importe
    assert cuenta_2.saldo() == saldo_cuenta_2 + traspaso.importe


def test_elimina_saldo_cta_entrada_al_momento_del_movimiento(mocker, cuenta, entrada):
    mock_eliminar = mocker.patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    saldo = Saldo.tomar(cuenta=cuenta, movimiento=entrada)
    entrada.delete()
    mock_eliminar.assert_called_once_with(saldo)


def test_elimina_saldo_cta_salida_al_momento_del_movimiento(mocker, cuenta, salida):
    mock_eliminar = mocker.patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    saldo = Saldo.tomar(cuenta=cuenta, movimiento=salida)
    salida.delete()
    mock_eliminar.assert_called_once_with(saldo)


def test_integrativo_elimina_saldo_cuentas_al_momento_del_movimiento(
        cuenta, cuenta_2, traspaso):
    deleted_pk = traspaso.pk
    traspaso.delete()
    with pytest.raises(Saldo.DoesNotExist):
        Saldo.objects.get(cuenta=cuenta, movimiento__pk=deleted_pk)
    with pytest.raises(Saldo.DoesNotExist):
        Saldo.objects.get(cuenta=cuenta_2, movimiento__pk=deleted_pk)


def test_resta_importe_de_saldos_posteriores_de_cta_entrada(cuenta, entrada, salida_posterior):
    saldo_posterior = Saldo.objects.get(cuenta=cuenta, movimiento=salida_posterior).importe
    entrada.delete()
    assert \
        Saldo.objects.get(cuenta=cuenta, movimiento=salida_posterior).importe == \
        saldo_posterior - entrada.importe


def test_suma_importe_a_saldos_posteriores_de_cta_salida(cuenta, salida, salida_posterior):
    saldo_posterior = Saldo.objects.get(cuenta=cuenta, movimiento=salida_posterior).importe
    salida.delete()
    assert \
        Saldo.objects.get(cuenta=cuenta, movimiento=salida_posterior).importe == \
        saldo_posterior + salida.importe


def test_en_mov_credito_elimina_contramovimiento(credito):
    id_contramovimiento = credito.id_contramov
    credito.delete()
    with pytest.raises(Movimiento.DoesNotExist):
        Movimiento.tomar(id=id_contramovimiento)


def test_si_al_eliminar_mov_credito_se_cancela_deuda_retira_titular_cta_entrada_de_deudores_de_titular_cta_salida(
        credito, titular, otro_titular):
    assert titular in otro_titular.deudores.all()
    credito.delete()
    assert titular not in otro_titular.deudores.all()


def test_repone_saldo_de_cuentas_credito(credito, contramov_credito):
    cta_deudora = contramov_credito.cta_salida
    cta_acreedora = contramov_credito.cta_entrada

    credito.delete()
    assert cta_deudora.saldo() == 0
    assert cta_acreedora.saldo() == 0


def test_da_error_si_se_intenta_eliminar_contramovimientos(contramov_credito):
    with pytest.raises(
            ValidationError,
            match='No se puede eliminar movimiento automático'):
        contramov_credito.delete()


def test_con_force_true_no_da_error_si_se_intenta_eliminar_contramovimientos(contramov_credito):
    try:
        contramov_credito.delete(force=True)
    except errors.ErrorMovimientoAutomatico:
        raise AssertionError(
            'No se eliminó contramovimiento a pesar de force=True')


@pytest.mark.parametrize('sentido', ['entrada', 'salida'])
def test_no_puede_eliminarse_movimiento_con_cuenta_acumulativa(
        sentido, request):
    mov = request.getfixturevalue(f'{sentido}_con_ca')
    with pytest.raises(
            errors.ErrorCuentaEsAcumulativa,
            match=errors.MOVIMIENTO_CON_CA_ELIMINADO
    ):
        mov.delete()
