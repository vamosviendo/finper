def test_devuelve_saldo_en_moneda_dada(cuenta, peso, dolar):
    assert cuenta.saldo_en(dolar) == cuenta.saldo * cuenta.moneda.cotizacion_en(dolar)
    assert cuenta.saldo_en(peso) == cuenta.saldo