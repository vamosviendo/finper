import pytest


@pytest.mark.parametrize("sentido", ["entrada", "salida"])
def test_devuelve_importe_de_la_cuenta_del_sentido_dado(traspaso, sentido):
    assert traspaso.importe_cta(sentido) == getattr(traspaso, f"importe_cta_{sentido}")

def test_da_error_si_se_pasa_argumento_no_permitido(traspaso):
    with pytest.raises(ValueError):
        traspaso.importe_cta("caca")
