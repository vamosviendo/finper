def test_devuelve_identidad_basada_en_movimiento_y_slug_de_cuenta(saldo):
    assert saldo.identidad == f"{saldo.movimiento.identidad}{saldo.cuenta.slug}"
