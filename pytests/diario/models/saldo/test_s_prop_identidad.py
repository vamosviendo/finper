def test_devuelve_identidad_basada_en_movimiento_y_sk_de_cuenta(saldo):
    assert saldo.identidad == f"{saldo.movimiento.identidad}{saldo.cuenta.sk}"
