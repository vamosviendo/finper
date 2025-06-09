from unittest.mock import call

from django.core.management import call_command

from diario.models import SaldoDiario, Movimiento


def test_borra_saldos_diarios_antes_de_recalcular(
        entrada, salida, entrada_otra_cuenta, salida_posterior, entrada_tardia_cuenta_ajena, mocker):
    saldos_diarios = SaldoDiario.todes()
    mock_delete = mocker.patch("diario.models.SaldoDiario.delete", autospec=True)
    call_command("regenerar_saldos_diarios")
    for sd in saldos_diarios:
        assert call(sd) in mock_delete.call_args_list


def test_calcula_saldos_diarios_a_partir_de_movimientos(
        entrada, salida, entrada_otra_cuenta, salida_posterior, entrada_tardia_cuenta_ajena, mocker):
    mock_calcular = mocker.patch("diario.models.SaldoDiario.calcular")
    call_command("regenerar_saldos_diarios")
    for mov in Movimiento.todes():
        campos_cuenta = [x for x in ("cta_entrada", "cta_salida") if getattr(mov, x) is not None]
        for cc in campos_cuenta:
            assert call(mov, cc) in mock_calcular.call_args_list


def test_importe_de_saldos_diarios_calculados_corresponde_a_movimientos(
        dia, cuenta, cuenta_2, entrada, salida, entrada_otra_cuenta,
        dia_posterior, salida_posterior,
        dia_tardio, cuenta_ajena, entrada_tardia_cuenta_ajena):
    saldo_dia_cuenta = SaldoDiario.tomar(dia=dia, cuenta=cuenta)
    importe_sdc = saldo_dia_cuenta.importe
    saldo_dia_cuenta_2 = SaldoDiario.tomar(dia=dia, cuenta=cuenta_2)
    importe_sdc2 = saldo_dia_cuenta_2.importe
    saldo_dia_posterior = SaldoDiario.tomar(dia=dia_posterior, cuenta=cuenta)
    importe_sdp = saldo_dia_posterior.importe
    saldo_dia_tardio= SaldoDiario.tomar(dia=dia_tardio, cuenta=cuenta_ajena)
    importe_sdt = saldo_dia_tardio.importe

    saldo_dia_cuenta.importe = importe_sdc + 25
    saldo_dia_cuenta.clean_save()
    saldo_dia_cuenta_2.importe = importe_sdc2 + 33
    saldo_dia_cuenta_2.clean_save()
    saldo_dia_posterior.importe = importe_sdp + 45
    saldo_dia_posterior.clean_save()
    saldo_dia_tardio.importe = importe_sdt + 55
    saldo_dia_tardio.clean_save()

    call_command("regenerar_saldos_diarios")

    assert saldo_dia_cuenta.tomar_de_bd().importe == importe_sdc
    assert saldo_dia_cuenta_2.tomar_de_bd().importe == importe_sdc2
    assert saldo_dia_posterior.tomar_de_bd().importe == importe_sdp
    assert saldo_dia_tardio.tomar_de_bd().importe == importe_sdt
