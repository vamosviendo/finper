from diario.models import SaldoDiario


def test_devuelve_saldo_diario_de_la_cuenta_en_el_dia_dado(cuenta, entrada):
    assert cuenta.saldo_diario(dia=entrada.dia) == SaldoDiario.tomar(cuenta=cuenta, dia=entrada.dia)

def test_si_no_hay_saldo_diario_de_la_cuenta_en_el_dia_devuelve_None(cuenta, entrada, dia_posterior):
    assert cuenta.saldo_diario(dia=dia_posterior) is None
