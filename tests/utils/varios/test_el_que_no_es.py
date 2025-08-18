import pytest

from utils.varios import el_que_no_es


def test_dados_dos_valores_y_una_referencia_devuelve_el_valor_que_es_distinto_a_la_referencia():
    assert el_que_no_es(1, valor1=1, valor2=2) == 2


def test_si_ambos_valores_son_distintos_a_referencia_da_valueerror():
    with pytest.raises(ValueError):
        el_que_no_es(1, 2, 3)


def test_si_ambos_valores_son_iguales_a_referencia_da_valuerror():
    with pytest.raises(ValueError):
        el_que_no_es(1, 1, 1)


def test_si_ambos_valores_son_de_distinto_tipo_da_typeerror():
    with pytest.raises(TypeError):
        el_que_no_es(1, 1, "a")
