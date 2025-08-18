from datetime import timedelta

from diario.models import SaldoDiario, Dia


def test_modifica_saldos_posteriores(saldo_diario, saldo_diario_posterior):
    importe = saldo_diario_posterior.importe

    SaldoDiario.crear(
        cuenta=saldo_diario.cuenta,
        dia=Dia.crear(fecha=saldo_diario.dia.fecha + timedelta(1)),
        importe=saldo_diario.importe + 100
    )

    saldo_diario_posterior.refresh_from_db()
    assert saldo_diario_posterior.importe == importe + 100
