def test_devuelve_sk_basada_en_movimiento_y_sk_de_cuenta(saldo):
    assert saldo.sk == f"{saldo.movimiento.sk}{saldo.cuenta.sk}"
