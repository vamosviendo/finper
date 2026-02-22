import pytest

from diario.models import SaldoDiario


@pytest.mark.parametrize("otros_movs", [[], ["salida"], ["traspaso_posterior"], ["salida", "traspaso_posterior"]])
def test_recalcula_saldos_diarios_de_cuenta(
        cuenta, entrada, salida_posterior, otros_movs, request):
    for otro_mov in otros_movs:
        request.getfixturevalue(otro_mov)
    saldo_diario = SaldoDiario.tomar(cuenta=cuenta, dia=entrada.dia)
    saldo_diario_posterior = SaldoDiario.tomar(cuenta=cuenta, dia=salida_posterior.dia)
    importe_saldo_diario = saldo_diario.importe
    saldo_diario.importe = 5
    saldo_diario.save()
    importe_saldo_diario_posterior = saldo_diario_posterior.importe
    saldo_diario_posterior.importe = 1000
    saldo_diario_posterior.save()

    cuenta.recalcular_saldos_diarios()

    saldo_diario = SaldoDiario.tomar(cuenta=saldo_diario.cuenta, dia=saldo_diario.dia)
    assert saldo_diario.importe == importe_saldo_diario
    saldo_diario_posterior = SaldoDiario.tomar(cuenta=saldo_diario_posterior.cuenta, dia=saldo_diario_posterior.dia)
    assert saldo_diario_posterior.importe == importe_saldo_diario_posterior


def test_no_recalcula_saldos_diarios_de_otras_cuentas(cuenta, cuenta_2, dia, entrada, entrada_otra_cuenta):
    saldo_diario_otra_cuenta = SaldoDiario.tomar(cuenta=cuenta_2, dia=dia)
    saldo_diario_otra_cuenta.importe = 5
    saldo_diario_otra_cuenta.save()

    cuenta.recalcular_saldos_diarios()

    saldo_diario_otra_cuenta.refresh_from_db()
    assert saldo_diario_otra_cuenta.importe == 5


def test_no_recalcula_saldo_diario_de_otra_cuenta_en_traspasos(cuenta, cuenta_2, dia, traspaso):
    saldo_diario_otra_cuenta = SaldoDiario.tomar(cuenta=cuenta_2, dia=dia)
    saldo_diario_otra_cuenta.importe = 5
    saldo_diario_otra_cuenta.save()

    cuenta.recalcular_saldos_diarios()

    saldo_diario_otra_cuenta.refresh_from_db()
    assert saldo_diario_otra_cuenta.importe == 5


def test_permite_recalcular_desde_una_fecha_especifica(
        mocker,  cuenta, dia_anterior, dia, dia_posterior, entrada_anterior, entrada, salida, salida_posterior):
    mock_delete = mocker.patch("diario.models.SaldoDiario.delete", autospec=True)
    mock_calcular = mocker.patch("diario.models.SaldoDiario.calcular")
    saldo_dia, saldo_dia_posterior = SaldoDiario.filtro(dia__gte=dia)

    cuenta.recalcular_saldos_diarios(desde=dia)

    assert mock_delete.call_args_list == [
        mocker.call(saldo_dia),
        mocker.call(saldo_dia_posterior),
    ]
    assert mock_calcular.call_args_list == [
        mocker.call(entrada, "cta_entrada"),
        mocker.call(salida, "cta_salida"),
        mocker.call(salida_posterior, "cta_salida")
    ]
