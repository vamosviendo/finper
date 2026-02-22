def test_devuelve_el_saldo_diario_de_la_misma_cuenta_anterior_al_actual(
        saldo_diario, saldo_diario_anterior, saldo_diario_temprano):
    assert saldo_diario.anterior() == saldo_diario_anterior


def test_si_no_hay_saldo_diario_anterior_de_la_misma_cuenta_devuelve_None(saldo_diario):
    assert saldo_diario.anterior() is None
