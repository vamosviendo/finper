from unittest.mock import patch

from django.test import TestCase

from diario.models import Cuenta, Movimiento
from diario.templatetags.historico import historico


@patch('diario.models.Cuenta.saldo_historico', autospec=True)
class TestHistorico(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta', 'cta')
        self.mov = Movimiento.crear('Ingreso', 100, self.cuenta)

    def test_devuelve_saldo_historico_de_cuenta_al_momento_del_movimiento(self, mock_saldo_historico):
        mock_saldo_historico.return_value = 255.54

        result = historico(self.cuenta, self.mov)

        mock_saldo_historico.assert_called_once_with(self.cuenta, self.mov)
        self.assertEqual(result, 255.54)
