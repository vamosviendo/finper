import pytest
from diario.templatetags.dict_key import dict_key
from diario.templatetags.historicos import cap_historico, historico, historico_general
from diario.templatetags.movimientos import movs_seleccionados
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


class TestFilterMovsSeleccionados:
    def test_devuelve_movimientos_de_una_cuenta_en_un_dia(
            self, dia, cuenta, entrada, salida, entrada_anterior, salida_posterior, entrada_otra_cuenta):
        assert list(movs_seleccionados(dia, cuenta)) == [entrada, salida]

    def test_si_cuenta_es_none_devuelve_todos_los_movimientos_del_dia(
            self, dia, entrada, salida, entrada_anterior, salida_posterior, entrada_otra_cuenta):
        assert list(movs_seleccionados(dia, None)) == [entrada, salida, entrada_otra_cuenta]

    def test_devuelve_movimientos_de_un_titular_en_un_dia(
            self, dia, titular, entrada, salida, entrada_anterior, salida_posterior,
            entrada_otra_cuenta, entrada_cuenta_ajena):
        assert list(movs_seleccionados(dia, titular)) == [entrada, salida, entrada_otra_cuenta]

    def test_si_titular_es_none_devuelve_todos_los_movimientos_del_dia(
            self, dia, titular, entrada, salida, entrada_anterior, salida_posterior,
            entrada_otra_cuenta, entrada_cuenta_ajena):
        assert list(movs_seleccionados(dia, None)) == [entrada, salida, entrada_otra_cuenta, entrada_cuenta_ajena]
