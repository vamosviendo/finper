from diario.models import Movimiento


def test_devuelve_suma_de_saldos_de_subcuentas_interactivas(cuenta_acumulativa_saldo_0, fecha):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    Movimiento.crear('saldo sc1', 100, sc1, fecha=fecha)
    Movimiento.crear('saldo sc2', 70, None, sc2, fecha=fecha)

    assert cuenta_acumulativa_saldo_0.saldo() == 100 - 70


def test_devuelve_suma_de_saldos_incluyendo_subcuentas_acumulativas(cuenta_acumulativa_saldo_0, fecha):
    sc1, sc2 = cuenta_acumulativa_saldo_0.subcuentas.all()
    Movimiento.crear('saldo sc1', 100, sc1, fecha=fecha)
    Movimiento.crear('saldo sc2', 70, None, sc2, fecha=fecha)

    sc11, sc12 = sc1.dividir_entre(
        ['subsubcuenta 1.1', 'sc11', 30],
        ['subsubcuenta 1.2', 'sc12'],
        fecha=fecha
    )
    Movimiento.crear('saldo sc11', 60, sc11, fecha=fecha)
    sc1 = sc1.tomar_del_slug()

    assert sc1.saldo() == 90 + 70
    assert cuenta_acumulativa_saldo_0.saldo() == 160 - 70
