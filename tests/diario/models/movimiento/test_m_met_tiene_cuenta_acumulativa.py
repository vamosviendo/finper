def test_devuelve_true_si_mov_tiene_una_cuenta_acumulativa(traspaso, cuenta, dicts_subcuentas):
    cuenta.dividir_entre(dicts_subcuentas)
    traspaso.refresh_from_db()
    assert traspaso.tiene_cuenta_acumulativa()


def test_devuelve_false_si_mov_no_tiene_cuenta_acumulativa(traspaso):
    assert not traspaso.tiene_cuenta_acumulativa()
