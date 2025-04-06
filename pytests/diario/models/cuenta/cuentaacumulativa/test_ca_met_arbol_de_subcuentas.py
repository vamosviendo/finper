def test_arbol_de_subcuentas_devuelve_set_con_todas_las_cuentas_dependientes(cuenta):
    lista_subcuentas = cuenta.dividir_entre(
        {'nombre': 'subcuenta 1', 'sk': 'sc1', 'saldo': 0},
        {'nombre': 'subcuenta 2', 'sk': 'sc2', },
    )
    cuenta = cuenta.tomar_del_sk()

    lista_subcuentas += lista_subcuentas[0].dividir_entre(
        {
            'nombre': 'subsubcuenta 1.1',
            'sk': 'ssc11',
            'saldo': 0,
        },
        {'nombre': 'subsubcuenta 1.2', 'sk': 'ssc12', },
    )
    lista_subcuentas[0] = lista_subcuentas[0].tomar_del_sk()
    lista_subcuentas[1] = lista_subcuentas[1].tomar_del_sk()
    lista_subcuentas += lista_subcuentas[1].dividir_entre(
        {
            'nombre': 'subsubcuenta 2.1',
            'sk': 'ssc21',
            'saldo': 0,
        },
        {'nombre': 'subsubcuenta 2.2', 'sk': 'ssc22', },
    )
    lista_subcuentas[1] = lista_subcuentas[1].tomar_del_sk()

    lista_subcuentas += lista_subcuentas[2].dividir_entre(
        {
            'nombre': 'subsubsubcuenta 1.1.1',
            'sk': 'sssc111',
            'saldo': 0,
        },
        {
            'nombre': 'subsubsubcuenta 1.1.2',
            'sk': 'sssc112',
        },
    )
    lista_subcuentas[2] = lista_subcuentas[2].tomar_del_sk()

    assert cuenta.arbol_de_subcuentas() == set(lista_subcuentas)
