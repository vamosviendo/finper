import pytest


def test_devuelve_true_si_el_mov_es_un_traspaso_entre_cuentas_en_distintas_monedas(
        mov_distintas_monedas_en_moneda_cta_entrada):
    mov = mov_distintas_monedas_en_moneda_cta_entrada
    assert mov.es_bimonetario() is True

@pytest.mark.parametrize("fixture_mov", ["entrada", "salida", "traspaso"])
def test_devuelve_false_en_cualquier_otro_caso(fixture_mov, request):
    mov = request.getfixturevalue(fixture_mov)
    assert mov.es_bimonetario() is False
