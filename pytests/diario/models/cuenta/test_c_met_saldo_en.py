def test_devuelve_saldo_en_moneda_dada_redondeado_en_2_decimales(cuenta_con_saldo, peso, dolar):
    assert \
        cuenta_con_saldo.saldo_en(dolar) == \
        round(cuenta_con_saldo.saldo * cuenta_con_saldo.moneda.cotizacion_en(dolar), 2)
    assert cuenta_con_saldo.saldo_en(peso) == cuenta_con_saldo.saldo
