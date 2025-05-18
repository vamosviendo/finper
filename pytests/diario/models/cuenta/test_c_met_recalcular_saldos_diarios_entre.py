from unittest.mock import call


def test_toma_como_importe_el_total_de_los_movimientos_del_dia_de_la_cuenta(
        cuenta, saldo_diario, saldo_diario_posterior, mocker):
    mock_importe_movs = mocker.patch("diario.models.cuenta.SaldoDiario.importe_movs", autospec=True)
    cuenta.recalcular_saldos_diarios_entre(saldo_diario.dia.fecha, saldo_diario_posterior.dia.fecha)
    assert mock_importe_movs.call_args_list == [call(saldo_diario), call(saldo_diario_posterior)]


def test_recalcula_saldos_diarios_de_cuenta_a_partir_de_fecha_inicial(cuenta, saldo_diario, saldo_diario_posterior):
    importe_sd = saldo_diario.importe
    saldo_diario.importe += 10
    saldo_diario.clean_save()
    importe_sdp = saldo_diario_posterior.importe
    saldo_diario_posterior.importe += 10
    saldo_diario_posterior.clean_save()

    cuenta.recalcular_saldos_diarios_entre(saldo_diario.dia.fecha, saldo_diario_posterior.dia.fecha)

    saldo_diario.refresh_from_db()
    assert saldo_diario.importe == importe_sd
    saldo_diario_posterior.refresh_from_db()
    assert saldo_diario_posterior.importe == importe_sdp


def test_no_recalcula_saldos_anteriores_a_fecha_inicial(
        cuenta, saldo_diario_anterior, saldo_diario, saldo_diario_posterior):
    saldo_diario_anterior.importe += 10
    importe_sda = saldo_diario_anterior.importe
    saldo_diario_anterior.clean_save()

    cuenta.recalcular_saldos_diarios_entre(saldo_diario.dia.fecha, saldo_diario_posterior.dia.fecha)

    saldo_diario_anterior.refresh_from_db()
    assert saldo_diario_anterior.importe == importe_sda


def test_no_recalcula_saldos_de_otras_cuentas(
        cuenta, cuenta_2, saldo_diario, saldo_diario_posterior, saldo_diario_otra_cuenta):
    saldo_diario_otra_cuenta.importe += 10
    importe_sdoc = saldo_diario_otra_cuenta.importe
    saldo_diario_otra_cuenta.clean_save()

    cuenta.recalcular_saldos_diarios_entre(saldo_diario.dia.fecha, saldo_diario_posterior.dia.fecha)

    saldo_diario_otra_cuenta.refresh_from_db()
    assert saldo_diario_otra_cuenta.importe == importe_sdoc

def test_no_recalcula_saldos_posteriores_a_fecha_final(
        cuenta, saldo_diario, saldo_diario_posterior, saldo_diario_tardio):
    saldo_diario_tardio.importe += 10
    importe_sdt = saldo_diario_tardio.importe
    saldo_diario_tardio.clean_save()

    cuenta.recalcular_saldos_diarios_entre(saldo_diario.dia.fecha, saldo_diario_posterior.dia.fecha)

    saldo_diario_tardio.refresh_from_db()
    assert saldo_diario_tardio.importe == importe_sdt
