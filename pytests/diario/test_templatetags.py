import pytest

from diario.templatetags.historicos import cap_historico, historico, historico_general

pytestmark = pytest.mark.django_db


class TestHistorico:

    def test_devuelve_string_con_saldo_historico_de_cuenta_al_momento_del_movimiento(
            self, mocker, cuenta, entrada, importe_aleatorio):
        mock_saldo_historico = mocker.patch('diario.models.Cuenta.saldo_en_mov', autospec=True)
        mock_saldo_historico.return_value = importe_aleatorio

        result = historico(cuenta, entrada)

        mock_saldo_historico.assert_called_once_with(cuenta, entrada)
        assert result == f'{importe_aleatorio:.2f}'.replace('.', ',')


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
            self, mocker, titular, cuenta, entrada, importe_aleatorio):
        mock_capital_historico = mocker.patch('diario.models.Titular.capital_historico', autospec=True)
        mock_capital_historico.return_value = importe_aleatorio

        result = cap_historico(titular, entrada)

        mock_capital_historico.assert_called_once_with(titular, entrada)
        assert result == f'{importe_aleatorio:.2f}'.replace('.', ',')
