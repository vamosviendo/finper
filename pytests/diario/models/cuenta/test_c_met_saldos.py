def test_devuelve_dict_con_saldo_de_cuenta_en_todas_las_monedas(cuenta_con_saldo, peso, dolar, euro, yen):
    assert cuenta_con_saldo.saldos() == {
        peso.monname: cuenta_con_saldo.saldo_en(peso, compra=False),
        dolar.monname: cuenta_con_saldo.saldo_en(dolar, compra=False),
        euro.monname: cuenta_con_saldo.saldo_en(euro, compra=False),
        yen.monname: cuenta_con_saldo.saldo_en(yen, compra=False),
    }

def test_si_recibe_movimiento_devuelve_saldo_historico_de_cuenta_en_todas_las_monedas(
        cuenta, entrada, salida, peso, dolar, euro):
    assert cuenta.saldos(entrada) == {
        peso.monname: cuenta.saldo_en_mov_en(entrada, peso, compra=False),
        dolar.monname: cuenta.saldo_en_mov_en(entrada, dolar, compra=False),
        euro.monname: cuenta.saldo_en_mov_en(entrada, euro, compra=False),
    }
