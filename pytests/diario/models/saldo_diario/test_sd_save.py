from datetime import timedelta

import pytest

from diario.models import SaldoDiario, Dia


def test_si_es_un_saldo_diario_nuevo_suma_a_saldos_posteriores_diferencia_entre_su_importe_y_el_del_saldo_anterior(
        saldo_diario, saldo_diario_posterior):
    importe = saldo_diario_posterior.importe

    saldo = SaldoDiario(
        cuenta=saldo_diario.cuenta,
        dia=Dia.crear(fecha=saldo_diario.dia.fecha + timedelta(1)),
        importe=saldo_diario.importe + 100
    )
    saldo.full_clean()
    saldo.save()

    saldo_diario_posterior.refresh_from_db()
    assert saldo_diario_posterior.importe == importe + 100


def test_si_es_un_saldo_diario_nuevo_y_no_hay_saldo_anterior_suma_su_importe_a_saldos_posteriores(saldo_diario):
    importe = saldo_diario.importe

    saldo = SaldoDiario(
        cuenta=saldo_diario.cuenta,
        dia=Dia.crear(fecha=saldo_diario.dia.fecha - timedelta(1)),
        importe=100
    )
    saldo.full_clean()
    saldo.save()

    saldo_diario.refresh_from_db()
    assert saldo_diario.importe == importe + 100


def test_si_es_un_saldo_diario_nuevo_y_hay_un_saldo_diario_anterior_suma_la_diferencia_entre_su_importe_y_el_anterior_a_saldos_posteriores(
        saldo_diario_anterior, saldo_diario_posterior, dia):
    importe_posterior = saldo_diario_posterior.importe

    saldo_diario = SaldoDiario(
        cuenta=saldo_diario_anterior.cuenta,
        dia=dia,
        importe=100
    )
    saldo_diario.full_clean()
    saldo_diario.save()

    saldo_diario_posterior.refresh_from_db()
    assert saldo_diario_posterior.importe == importe_posterior + (saldo_diario.importe - saldo_diario_anterior.importe)


@pytest.mark.parametrize("cantidad", [100, -100])
def test_si_cambia_el_importe_se_modifican_importes_de_saldos_diarios_posteriores_de_la_cuenta(
        cantidad, saldo_diario, saldo_diario_posterior):
    importe_posterior = saldo_diario_posterior.importe
    saldo_diario.importe += cantidad
    saldo_diario.full_clean()
    saldo_diario.save()
    saldo_diario_posterior.refresh_from_db()
    assert saldo_diario_posterior.importe == importe_posterior + cantidad


def test_recorre_una_sola_vez_saldos_posteriores_de_la_cuenta(
        saldo_diario_anterior, entrada, salida_posterior, entrada_tardia, mocker, monkeypatch):
    calls = 0
    original = SaldoDiario._actualizar_posteriores

    def wrapper(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(SaldoDiario, "_actualizar_posteriores", wrapper)

    saldo_diario_anterior.eliminar()

    assert calls == 1
