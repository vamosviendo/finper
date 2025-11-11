def test_si_se_desactiva_cuenta_acumulativa_se_desactivan_todas_sus_subcuentas(cuenta_acumulativa_saldo_0):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()

    cuenta_acumulativa_saldo_0.activa = False
    cuenta_acumulativa_saldo_0.clean_save()

    for sc in sc1, sc2:
        sc.refresh_from_db()
        assert sc.activa is False


def test_si_se_desactivan_todas_las_subcuentas_de_una_cuenta_acumulativa_se_desactiva_la_cuenta_acumulativa(cuenta_acumulativa_saldo_0):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()

    for sc in sc1, sc2:
        sc.activa = False
        sc.clean_save()

    cuenta_acumulativa_saldo_0.refresh_from_db()
    assert cuenta_acumulativa_saldo_0.activa is False


def test_si_en_una_cuenta_acumulativa_inactiva_se_activa_una_subcuenta_se_activa_la_cuenta_acumulativa(cuenta_acumulativa_saldo_0):
    cuenta_acumulativa_saldo_0.activa = False
    cuenta_acumulativa_saldo_0.clean_save()

    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    sc1.activa = True
    sc1.clean_save()

    cuenta_acumulativa_saldo_0.refresh_from_db()
    assert cuenta_acumulativa_saldo_0.activa is True


def test_si_en_una_cuenta_acumulativa_inactiva_se_activa_una_subcuenta_las_otras_subcuentas_permanecen_inactivas(
        cuenta_acumulativa_saldo_0):
    cuenta_acumulativa_saldo_0.activa = False
    cuenta_acumulativa_saldo_0.clean_save()

    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    sc1.activa = True
    sc1.clean_save()

    sc2.refresh_from_db()
    assert sc2.activa is False
