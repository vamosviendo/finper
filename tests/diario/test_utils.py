from unittest.mock import patch

from django.test import TestCase

from diario.models import Cuenta
from diario.utils import verificar_saldos


@patch('diario.models.CuentaInteractiva.saldo_ok')
class TestVerificarSaldos(TestCase):

    def setUp(self):
        super().setUp()
        self.cta1 = Cuenta.crear('Afectivo', 'A')
        self.cta2 = Cuenta.crear('Banco', 'B')
        self.cta3 = Cuenta.crear('Cuenta corriente', 'C')

    def test_devuelve_lista_vacia_si_todos_los_saldos_ok(self, mock_saldo_ok):
        mock_saldo_ok.return_value = True
        ctas_erroneas = verificar_saldos()
        self.assertEqual(ctas_erroneas, [])

    def test_devuelve_lista_de_cuentas_con_saldos_incorrectos(
            self, mock_saldo_ok):
        mock_saldo_ok.side_effect = [False, False, True]
        ctas_erroneas = verificar_saldos()
        self.assertIn(self.cta1, ctas_erroneas)
        self.assertIn(self.cta2, ctas_erroneas)
        self.assertNotIn(self.cta3, ctas_erroneas)
