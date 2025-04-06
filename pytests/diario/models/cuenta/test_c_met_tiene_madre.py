def test_devuelve_true_si_tiene_cta_madre_y_false_si_no(cuenta):
    sc1, sc2 = cuenta.dividir_entre(
        {'nombre': 'subcuenta 1', 'sk': 'sc1', 'saldo': 40},
        {'nombre': 'subcuenta 2', 'sk': 'sc2'},
    )
    cuenta = cuenta.tomar_del_sk()

    assert sc1.tiene_madre()
    assert sc2.tiene_madre()
    assert not cuenta.tiene_madre()
