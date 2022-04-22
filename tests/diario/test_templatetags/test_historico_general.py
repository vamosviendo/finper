from datetime import date
from unittest.mock import patch

from django.test import TestCase

from diario.models import Cuenta, Movimiento
from diario.templatetags.historico_general import historico_general


@patch('diario.templatetags.historico_general.saldo_general_historico')
class TestHistoricoGeneral(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta', 'cta')
        self.mov = Movimiento.crear(
            'Ingreso', 100, self.cuenta,
            fecha=date(2010, 11, 11)
        )

    def test_llama_a_saldo_historico_general_para_obtener_saldo_historico(self, mock_saldo_historico):
        mock_saldo_historico.return_value = 0

        historico_general(self.mov)

        mock_saldo_historico.assert_called_once_with(self.mov)

    def test_devuelve_saldo_historico_general_recuperado(self, mock_saldo_historico):
        mock_saldo_historico.return_value = 255.54
        self.assertEqual(
            historico_general(self.mov),
            '255,54'
        )
