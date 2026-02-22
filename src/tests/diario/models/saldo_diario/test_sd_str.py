def test_devuelve_cadena_con_datos_del_saldo_diario(saldo_diario):
    assert \
        saldo_diario.__str__() == \
        f"{saldo_diario.cuenta} al {saldo_diario.dia}: {saldo_diario.importe}"
