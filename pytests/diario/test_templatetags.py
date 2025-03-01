import pytest

from diario.templatetags.dict_key import dict_key
from diario.templatetags.historicos import cap_historico, historico, historico_general
from utils.numeros import float_format

pytestmark = pytest.mark.django_db


class TestHistorico:
    def test_devuelve_string_con_saldo_historico_de_cuenta_al_momento_del_movimiento(
            self, cuenta, entrada, salida_posterior):
        assert historico(cuenta, entrada) == float_format(cuenta.saldo_en_mov(entrada))

    def test_si_movimiento_es_None_devuelve_saldo_actual_de_cuenta(self, cuenta, entrada, salida_posterior):
        assert historico(cuenta, None) != float_format(cuenta.saldo_en_mov(entrada))
        assert historico(cuenta, None) == float_format(cuenta.saldo)

class TestHistoricoGeneral:
    def test_llama_a_saldo_historico_general_para_obtener_saldo_historico(
            self, mocker, entrada):
        mock_saldo_historico = mocker.patch(
            'diario.templatetags.historicos.saldo_general_historico'
        )
        mock_saldo_historico.return_value = 0

        historico_general(entrada)

        mock_saldo_historico.assert_called_once_with(entrada)

    def test_devuelve_string_con_saldo_historico_general_recuperado(
            self, mocker, entrada, importe_aleatorio):
        mock_saldo_historico = mocker.patch(
            'diario.templatetags.historicos.saldo_general_historico'
        )
        mock_saldo_historico.return_value = importe_aleatorio
        assert \
            historico_general(entrada) == \
            f'{importe_aleatorio:.2f}'.replace('.', ',')


class TestCapHistorico:
    def test_devuelve_string_con_capital_historico_de_titular_al_momento_del_movimiento(
            self, titular, cuenta, entrada, salida_posterior):
        assert cap_historico(titular, entrada) == float_format(titular.capital_historico(entrada))

    def test_si_movimiento_es_None_devuelve_capital_actual_de_titular(
            self, titular, cuenta, entrada, salida_posterior):
        assert cap_historico(titular, None) == float_format(titular.capital)


class TestDictKey:
    def test_devuelve_el_valor_de_una_clave_de_diccionario(self):
        dicc = {'val_1': 1, 'val_2': 2, 'val_3': 'a'}
        assert dict_key(dicc, 'val_1') == 1
        assert dict_key(dicc, 'val_2') == 2
        assert dict_key(dicc, 'val_3') == 'a'
