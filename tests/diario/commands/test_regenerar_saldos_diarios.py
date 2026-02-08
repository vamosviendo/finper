from datetime import timedelta

import pytest
from django.core.management import call_command

from diario.models import SaldoDiario, Movimiento


def test_borra_saldos_diarios_antes_de_recalcular(
        entrada, salida, entrada_otra_cuenta, salida_posterior, entrada_tardia_cuenta_ajena, mocker):
    saldos_diarios = SaldoDiario.todes()
    mock_delete = mocker.patch("diario.models.SaldoDiario.delete", autospec=True)
    call_command("regenerar_saldos_diarios")
    for sd in saldos_diarios:
        assert mocker.call(sd) in mock_delete.call_args_list


def test_calcula_saldos_diarios_a_partir_de_movimientos(
        entrada, salida, entrada_otra_cuenta, salida_posterior, entrada_tardia_cuenta_ajena, mocker):
    mock_calcular = mocker.patch("diario.models.SaldoDiario.calcular")
    call_command("regenerar_saldos_diarios")
    for mov in Movimiento.todes():
        campos_cuenta = [x for x in ("cta_entrada", "cta_salida") if getattr(mov, x) is not None]
        for cc in campos_cuenta:
            assert mocker.call(mov, cc) in mock_calcular.call_args_list


def test_importe_de_saldos_diarios_calculados_corresponde_a_movimientos(
        dia, cuenta, cuenta_2, entrada, salida, traspaso, entrada_otra_cuenta,
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


def test_permite_recalcular_saldos_diarios_de_una_cuenta_dada(
        dia, cuenta, cuenta_2, entrada, salida, traspaso, entrada_otra_cuenta):
    saldo_dia_cuenta = SaldoDiario.tomar(dia=dia, cuenta=cuenta)
    importe_sdc = saldo_dia_cuenta.importe
    saldo_dia_cuenta_2 = SaldoDiario.tomar(dia=dia, cuenta=cuenta_2)
    importe_sdc2 = saldo_dia_cuenta_2.importe

    saldo_dia_cuenta.importe += 10
    saldo_dia_cuenta.clean_save()
    saldo_dia_cuenta_2.importe += 20
    saldo_dia_cuenta_2.clean_save()

    call_command("regenerar_saldos_diarios", cuenta=cuenta.sk)

    assert saldo_dia_cuenta.tomar_de_bd().importe == importe_sdc
    assert saldo_dia_cuenta_2.tomar_de_bd().importe == importe_sdc2 + 20


def test_permite_recalcular_saldos_diarios_a_partir_de_una_fecha_dada(
        mocker, dia_anterior, dia, dia_posterior, cuenta,
        entrada_anterior, entrada, salida, traspaso, salida_posterior):
    mock_delete = mocker.patch("diario.models.SaldoDiario.delete", autospec=True)
    mock_calcular = mocker.patch("diario.models.SaldoDiario.calcular")

    saldo_dia, saldo_otra_cuenta, saldo_dia_posterior = SaldoDiario.filtro(dia__gte=dia)

    call_command("regenerar_saldos_diarios", desde=str(dia))

    assert mock_delete.call_args_list == [
        mocker.call(saldo_dia),
        mocker.call(saldo_dia_posterior),
        mocker.call(saldo_otra_cuenta),
    ]
    assert mock_calcular.call_args_list == [
        mocker.call(entrada, "cta_entrada"),
        mocker.call(salida, "cta_salida"),
        mocker.call(traspaso, "cta_entrada"),
        mocker.call(salida_posterior, "cta_salida"),
        mocker.call(traspaso, "cta_salida"),
    ]


def test_permite_recalcular_saldos_diarios_de_una_cuenta_a_partir_de_una_fecha_dada(
        mocker, cuenta, cuenta_2, dia_anterior, dia, dia_posterior,
        entrada_anterior, entrada_anterior_otra_cuenta, entrada, salida,
        traspaso, entrada_otra_cuenta, salida_posterior, entrada_posterior_otra_cuenta):
    mock_delete = mocker.patch("diario.models.SaldoDiario.delete", autospec=True)
    mock_calcular = mocker.patch("diario.models.SaldoDiario.calcular")

    saldo_dia_cuenta, saldo_dia_posterior_cuenta = SaldoDiario.filtro(dia__gte=dia, cuenta=cuenta)

    call_command("regenerar_saldos_diarios", cuenta=cuenta.sk, desde=str(dia))

    assert mock_delete.call_args_list == [
        mocker.call(saldo_dia_cuenta),
        mocker.call(saldo_dia_posterior_cuenta),
    ]
    assert mock_calcular.call_args_list == [
        mocker.call(entrada, "cta_entrada"),
        mocker.call(salida, "cta_salida"),
        mocker.call(traspaso, "cta_entrada"),
        mocker.call(salida_posterior, "cta_salida")
    ]


def test_si_se_pasa_sk_de_cuenta_inexistente_sale_con_error():
    with pytest.raises(ValueError, match="SK ska no existe"):
        call_command("regenerar_saldos_diarios", cuenta="ska")


def test_si_se_pasa_fecha_mal_formateada_da_error():
    with pytest.raises(ValueError, match="Fecha mal formateiada. Debe ser YYYY-MM-DD"):
        call_command("regenerar_saldos_diarios", desde="202h-05-r")


def test_si_se_pasa_fecha_de_dia_inexistente_sale_con_error(
        mocker, dia_anterior, dia, dia_posterior, entrada_anterior, entrada, salida_posterior):
     mock_recalcular = mocker.patch("diario.models.cuenta.Cuenta.recalcular_saldos_diarios")
     fecha_desde = dia_anterior.fecha + timedelta(1)
     call_command("regenerar_saldos_diarios", desde=fecha_desde.strftime("%Y-%m-%d"))
     mock_recalcular.assert_called_with(desde=dia)
