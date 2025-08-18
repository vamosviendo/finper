def test_devuelve_sk_basada_en_sk_de_dia_y_sk_de_cuenta(saldo_diario):
    assert saldo_diario.sk == f"{saldo_diario.dia.sk}{saldo_diario.cuenta.sk}"
