import pytest
from django.core.exceptions import ValidationError

from diario.models import Movimiento, SaldoDiario
from utils import errors
from utils.helpers_tests import signo
from utils.varios import el_que_no_es


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


def test_si_se_borra_el_unico_movimiento_del_dia_de_la_cuenta_elimina_saldo_diario_de_la_cuenta(
        mocker, cuenta, salida, entrada_otra_cuenta):
    mock_eliminar = mocker.patch('diario.models.movimiento.SaldoDiario.eliminar', autospec=True)
    saldo = SaldoDiario.tomar(cuenta=cuenta, dia=salida.dia)
    salida.delete()
    mock_eliminar.assert_called_once_with(saldo)


def test_si_se_borra_el_unico_movimiento_del_dia_de_la_cuenta_no_se_elimina_saldo_diario_de_otras_cuentas(
        mocker, cuenta, cuenta_2, salida, entrada_otra_cuenta):
    mock_eliminar = mocker.patch('diario.models.movimiento.SaldoDiario.eliminar', autospec=True)
    saldo = SaldoDiario.tomar(cuenta=cuenta_2, dia=salida.dia)
    salida.delete()
    assert mocker.call(saldo) not in mock_eliminar.call_args_list


def test_si_hay_mas_movimientos_de_la_cuenta_en_el_dia_no_se_elimina_saldo_diario_de_la_cuenta(
        mocker, cuenta, salida, entrada):
    mock_eliminar = mocker.patch('diario.models.movimiento.SaldoDiario.eliminar', autospec=True)
    salida.delete()
    mock_eliminar.assert_not_called()


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_si_hay_mas_movimientos_de_la_cuenta_en_el_dia_resta_importe_del_saldo_diario_de_la_cuenta(
        sentido, cuenta, request):
    mov = request.getfixturevalue(sentido)
    request.getfixturevalue(el_que_no_es(sentido, "entrada", "salida"))
    saldo = SaldoDiario.tomar(cuenta=cuenta, dia=mov.dia)
    importe = saldo.importe

    mov.delete()
    saldo.refresh_from_db()

    assert saldo.importe == importe - mov.importe_cta(sentido)


def test_si_resta_importe_del_saldo_diario_de_la_cuenta_modifica_saldos_posteriores_de_la_cuenta(
        cuenta, salida, entrada, salida_posterior):
    saldo_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
    importe_posterior = saldo_posterior.importe

    salida.delete()

    saldo_posterior.refresh_from_db()
    assert saldo_posterior.importe == importe_posterior - salida.importe_cta_salida


def test_si_se_elimina_traspaso_entre_cuentas_con_unico_movimiento_en_el_dia_se_eliminan_saldos_diarios_de_ambas_cuentas(
        traspaso, mocker):
    mock_eliminar = mocker.patch('diario.models.movimiento.SaldoDiario.eliminar', autospec=True)
    saldo1 = SaldoDiario.tomar(cuenta = traspaso.cta_entrada, dia=traspaso.dia)
    saldo2 = SaldoDiario.tomar(cuenta = traspaso.cta_salida, dia=traspaso.dia)

    traspaso.delete()

    assert mock_eliminar.call_args_list == [mocker.call(saldo1), mocker.call(saldo2)]


def test_si_se_elimina_traspaso_entre_cuentas_con_mas_movimientos_en_el_dia_no_se_elimina_ningun_saldo(
        entrada, entrada_otra_cuenta, traspaso, mocker):
    mock_eliminar = mocker.patch('diario.models.movimiento.SaldoDiario.eliminar', autospec=True)
    traspaso.delete()
    mock_eliminar.assert_not_called()


def test_si_se_elimina_traspaso_entre_cuentas_con_mas_movimientos_en_el_dia_se_resta_importe_de_saldos_diarios_de_ambas_cuentas(
        entrada, entrada_otra_cuenta, traspaso):
    saldo1 = SaldoDiario.tomar(cuenta=traspaso.cta_entrada, dia=traspaso.dia)
    saldo2 = SaldoDiario.tomar(cuenta=traspaso.cta_salida, dia=traspaso.dia)
    importe1 = saldo1.importe
    importe2 = saldo2.importe
    importe_cta_entrada = traspaso.importe_cta_entrada
    importe_cta_salida = traspaso.importe_cta_salida

    traspaso.delete()

    saldo1.refresh_from_db()
    saldo2.refresh_from_db()
    assert saldo1.importe == importe1 - importe_cta_entrada
    assert saldo2.importe == importe2 - importe_cta_salida


@pytest.mark.parametrize("otro_movimiento", ["entrada", "entrada_otra_cuenta"])
def test_si_se_elimina_traspaso_entre_cuenta_con_unico_movimiento_en_el_dia_y_cuenta_con_mas_movimientos_en_el_dia_se_elimina_un_saldo_diario_y_se_modifica_el_importe_del_otro(
        traspaso, otro_movimiento, request, mocker):
    mock_eliminar = mocker.patch('diario.models.movimiento.SaldoDiario.eliminar', autospec=True)
    request.getfixturevalue(otro_movimiento)
    sentido = "entrada" if otro_movimiento == "entrada" else "salida"
    cuenta = getattr(traspaso, f"cta_{sentido}")
    otra_cuenta = getattr(traspaso, f"cta_{el_que_no_es(sentido, 'entrada', 'salida')}")
    saldo = SaldoDiario.tomar(cuenta=cuenta, dia=traspaso.dia)
    s = signo(sentido == "entrada")
    importe = saldo.importe
    otro_saldo = SaldoDiario.tomar(cuenta=otra_cuenta, dia=traspaso.dia)
    importe_mov = traspaso.importe

    traspaso.delete()

    mock_eliminar.assert_called_once_with(otro_saldo)
    saldo.refresh_from_db()
    assert saldo.importe == importe - s*importe_mov


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
@pytest.mark.parametrize("otros_movs", [[], ["traspaso"], ["entrada_anterior"], ["entrada_anterior", "traspaso"]])
def test_resta_importe_de_saldos_diarios_posteriores_de_cta_entrada(
        cuenta, sentido, otros_movs, salida_posterior, request):
    for otro_mov in otros_movs:
        request.getfixturevalue(otro_mov)
    mov = request.getfixturevalue(sentido)
    saldo_posterior = SaldoDiario.objects.get(cuenta=cuenta, dia=salida_posterior.dia).importe
    mov.delete()
    assert \
        SaldoDiario.objects.get(cuenta=cuenta, dia=salida_posterior.dia).importe == \
        saldo_posterior - mov.importe_cta(sentido)


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
