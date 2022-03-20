from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento, Saldo


class TestSaldoBasic(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta normal', 'cn')

    def test_guarda_y_recupera_saldos(self):
        saldo = Saldo()
        saldo.cuenta = self.cuenta
        saldo.fecha = date(2010, 11, 11)
        saldo.importe = 100
        saldo.save()

        self.assertEqual(Saldo.cantidad(), 1)

        saldo_recuperado = saldo.tomar(cuenta=self.cuenta, fecha=date(2010, 11, 11))

        self.assertEqual(saldo_recuperado.importe, 100)

    def test_no_admite_mas_de_un_saldo_por_cuenta_en_cada_fecha(self):
        Saldo.crear(cuenta=self.cuenta, fecha=date(2010, 11, 11), importe=10)

        saldo = Saldo()
        saldo.cuenta = self.cuenta
        saldo.fecha = date(2010, 11, 11)
        saldo.importe = 15

        with self.assertRaises(ValidationError):
            saldo.full_clean()

    def test_saldos_se_ordenan_por_fecha(self):
        saldo1 = Saldo.crear(
            cuenta=self.cuenta, fecha=date(2010, 11, 10), importe=10)
        saldo2 = Saldo.crear(
            cuenta=self.cuenta, fecha=date(2010, 11, 2), importe=15)
        saldo3 = Saldo.crear(
            cuenta=self.cuenta, fecha=date(2010, 11, 5), importe=5)
        self.assertEqual(
            list(Saldo.todes()),
            [saldo2, saldo3, saldo1]
        )

    def test_dentro_de_fecha_saldos_se_ordenan_por_cuenta(self):
        cuenta2 = Cuenta.crear('cuenta 2', 'c2')
        cuenta3 = Cuenta.crear('cuenta 3', 'c3')
        saldo1 = Saldo.crear(
            cuenta=self.cuenta, fecha=date(2010, 11, 1), importe=10)
        saldo2 = Saldo.crear(
            cuenta=cuenta3, fecha=date(2010, 11, 1), importe=10)
        saldo3 = Saldo.crear(
            cuenta=cuenta2, fecha=date(2010, 11, 1), importe=10)
        self.assertEqual(
            list(Saldo.todes()),
            [saldo3, saldo2, saldo1]
        )


class TestSaldoTomar(TestCase):

    def test_si_no_encuentra_saldo_de_cuenta_en_fecha_busca_saldo_de_ultima_fecha_anterior(self):
        cuenta1 = Cuenta.crear('cuenta 1', 'c1')
        saldo2 = Saldo.crear(cuenta=cuenta1, fecha=date(2020, 1, 2), importe=150)
        Saldo.crear(cuenta=cuenta1, fecha=date(2020, 1, 1), importe=100)
        self.assertEqual(
            Saldo.tomar(cuenta=cuenta1, fecha=date(2020, 1, 10)),
            saldo2
        )

    def test_si_no_encuentra_saldo_de_cuenta_en_fecha_ni_en_fechas_anteriores_lanza_excepcion(self):
        cuenta1 = Cuenta.crear('cuenta 1', 'c1')
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.tomar(cuenta=cuenta1, fecha=date(2020, 1, 10))


class TestSaldoMetodoRegistrar(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta normal', 'cn')

    @patch('diario.models.Saldo.crear')
    def test_primer_registro_en_fecha_genera_nuevo_saldo(self, mock_crear):
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 100)
        mock_crear.assert_called_once_with(
            cuenta=self.cuenta,
            fecha=date(2010, 11, 11),
            importe=100
        )

    @patch('diario.models.Saldo.crear')
    @patch('diario.models.saldo.len')
    def test_segundo_registro_en_fecha_no_genera_nuevo_saldo(self, mock_len, mock_crear):
        mock_len.return_value = 1
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 100)
        mock_crear.assert_not_called()
