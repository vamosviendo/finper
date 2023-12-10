def test_devuelve_saldo_en_movimiento_dado_en_moneda_dada_redondeado_en_2_decimales(cuenta, entrada, salida, peso, dolar):
    assert \
        cuenta.saldo_en_mov_en(salida, dolar) == \
        round(cuenta.saldo_en_mov(salida) * cuenta.moneda.cotizacion_en(dolar), 2)
    assert cuenta.saldo_en_mov_en(entrada, peso) == cuenta.saldo_en_mov(entrada)
