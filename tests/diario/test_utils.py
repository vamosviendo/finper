from datetime import date
from unittest.mock import patch

from django.test import TestCase

from diario.models import Cuenta, Movimiento, Saldo
from diario.utils import verificar_saldos, saldo_general_historico
from utils.helpers_tests import dividir_en_dos_subcuentas


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


class TestSaldoGeneralHistorico(TestCase):

    def setUp(self):
        self.fecha1 = date(2020, 5, 2)
        self.fecha2 = date(2020, 5, 8)
        self.fecha3 = date(2020, 5, 10)
        self.cuenta1 = Cuenta.crear(
            'cuenta 1', 'c1', fecha_creacion=self.fecha1)
        self.cuenta2 = Cuenta.crear(
            'cuenta 2', 'c2', fecha_creacion=self.fecha1)
        self.cuenta3 = Cuenta.crear(
            'cuenta 3', 'c3', fecha_creacion=self.fecha1)
        self.mov1 = Movimiento.crear(
            'Mov cta 1', 10, self.cuenta1, fecha=self.fecha1)
        self.mov2 = Movimiento.crear(
            'Mov cta 2', 20, self.cuenta2, fecha=self.fecha1)
        self.mov3 = Movimiento.crear(
            'Mov cta 3', 15, None, self.cuenta3, fecha=self.fecha1)

    def test_devuelve_suma_de_saldos_historicos_de_cuentas_al_momento_del_movimiento(self):
        self.assertEqual(
            saldo_general_historico(self.mov1),
            Saldo.tomar(cuenta=self.cuenta1, fecha=self.fecha1).importe
            # 10
        )

        self.assertEqual(
            saldo_general_historico(self.mov2),
            Saldo.tomar(cuenta=self.cuenta1, fecha=self.fecha1).importe +
                Saldo.tomar(cuenta=self.cuenta2, fecha=self.fecha1).importe
            # 10+20
        )

        self.assertEqual(
            saldo_general_historico(self.mov3),
            Saldo.tomar(cuenta=self.cuenta1, fecha=self.fecha1).importe +
                Saldo.tomar(cuenta=self.cuenta2, fecha=self.fecha1).importe +
                Saldo.tomar(cuenta=self.cuenta3, fecha=self.fecha1).importe
            # 10+20-15
        )

    def test_suma_una_sola_vez_saldo_de_cuentas_acumulativas(self):
        self.cuenta1 = dividir_en_dos_subcuentas(
            self.cuenta1, saldo=3, fecha=self.fecha2)
        mov = Movimiento.crear('Otro mov', 5, self.cuenta3, fecha=self.fecha3)

        self.assertEqual(
            saldo_general_historico(mov),
        10+20-10
        )
