from diario.models import SaldoDiario


def test_devuelve_la_version_persistente_de_un_saldo_diario_basandose_en_cuenta_y_dia(saldo_diario):
    assert saldo_diario.tomar_de_bd() == SaldoDiario.tomar(cuenta=saldo_diario.cuenta, dia=saldo_diario.dia)


def test_si_no_hay_version_persistente_de_un_saldo_diario_devuelve_None(cuenta, dia):
    saldo_diario = SaldoDiario(cuenta=cuenta, dia=dia, importe=100)
    assert saldo_diario.tomar_de_bd() is None
