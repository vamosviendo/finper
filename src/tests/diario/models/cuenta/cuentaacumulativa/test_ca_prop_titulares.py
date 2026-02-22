def test_devuelve_lista_de_titulares_de_subcuentas_sin_elementos_repetidos(cuenta_acumulativa, titular, otro_titular):
    cuenta_acumulativa.agregar_subcuenta('subcuenta 3', 'sc3', titular)
    sc1, sc2, sc3 = cuenta_acumulativa.subcuentas.all()
    sc1.titular = titular
    sc1.save()
    sc2.titular = otro_titular
    sc2.save()
    sc3.titular = titular
    sc3.save()

    assert cuenta_acumulativa.titulares == [titular, otro_titular]


def test_si_subcuenta_es_acumulativa_incluye_titulares_de_subcuenta(
        cuenta_acumulativa, titular, otro_titular, titular_gordo):
    sc1, sc2 = cuenta_acumulativa.subcuentas.all()
    sc2.titular = otro_titular
    sc2.save()

    sc1 = sc1.dividir_y_actualizar(
        ['subsubcuenta 1.1', 'ssc11', 50],
        ['subsubcuenta 1.2', 'ssc12']
    )
    ssc11, ssc12 = sc1.subcuentas.all()
    ssc11.titular = titular
    ssc11.save()
    ssc12.titular = titular_gordo
    ssc12.save()

    assert cuenta_acumulativa.titulares == [titular, otro_titular, titular_gordo]
