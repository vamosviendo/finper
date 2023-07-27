def test_devuelve_suma_de_saldos_historicos_de_cuentas_de_titular_al_momento_de_un_movimiento(
        titular, entrada, entrada_otra_cuenta, salida_posterior, entrada_tardia, cuenta_ajena):
    cuenta = entrada.cta_entrada
    otra_cuenta = entrada_otra_cuenta.cta_entrada

    assert titular.capital_historico(salida_posterior) == \
           cuenta.saldo_en_mov(salida_posterior) + otra_cuenta.saldo_en_mov(salida_posterior)
