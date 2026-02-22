import pytest


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_devuelve_string_con_sentido_de_la_cuenta_en_un_movimiento_dado(sentido, traspaso, cuenta, request):
    mov = request.getfixturevalue(sentido)
    assert cuenta.sentido_en_mov(mov) == sentido
    assert cuenta.sentido_en_mov(traspaso) == "entrada"

@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_devuelve_None_si_la_cuenta_no_interviene_en_el_movimiento_dado(sentido, traspaso, cuenta_2, request):
    mov = request.getfixturevalue(sentido)
    assert cuenta_2.sentido_en_mov(mov) is None
