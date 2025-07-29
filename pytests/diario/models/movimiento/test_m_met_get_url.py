import pytest


def test_devuelve_url_absoluta_de_movimiento(entrada):
    assert entrada.get_url() == entrada.get_absolute_url()

@pytest.mark.parametrize("fixt", ["titular", "cuenta"])
def test_si_se_le_pasa_titular_o_cuenta_devuelve_url_de_titular_o_cuenta_con_movimiento(entrada, fixt, request):
    ente = request.getfixturevalue(fixt)
    assert entrada.get_url(ente) == ente.get_url_with_mov(entrada)
