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

    def test_saldo_creado_suma_importe_recibido_a_ultimo_saldo_anterior_de_cuenta(self):
        Saldo.registrar(self.cuenta, date(2010, 11, 1), 100)

        with patch('diario.models.Saldo.crear') as mock_crear:
            Saldo.registrar(self.cuenta, date(2010, 11, 11), 100)
            mock_crear.assert_called_once_with(
                cuenta=self.cuenta,
                fecha=date(2010, 11, 11),
                importe=200
            )

    def test_segundo_registro_de_cuenta_en_fecha_no_genera_nuevo_saldo(self):
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 100)
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 10)

        self.assertEqual(Saldo.cantidad(), 1)

    def test_segundo_registro_de_otra_cuenta_en_fecha_genera_nuevo_saldo(self):
        cuenta2 = Cuenta.crear('cuenta2', 'c2')

        Saldo.registrar(self.cuenta, date(2010, 11, 11), 10)
        Saldo.registrar(cuenta2, date(2010, 11, 11), 10)

        self.assertEqual(Saldo.cantidad(), 2)

    def test_segundo_registro_en_fecha_suma_importe_a_saldo(self):
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 10)
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 5)

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta, fecha=date(2010, 11, 11)).importe,
            15
        )

    def test_devuelve_saldo_creado(self):
        saldo = Saldo.registrar(self.cuenta, date(2010, 11, 1), 100)
        self.assertEqual(
            saldo,
            Saldo.tomar(cuenta=self.cuenta, fecha=date(2010, 11, 1))
        )

    def test_devuelve_saldo_actualizado(self):
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 10)
        saldo = Saldo.registrar(self.cuenta, date(2010, 11, 11), 5)

        self.assertEqual(
            saldo,
            Saldo.tomar(cuenta=self.cuenta, fecha=date(2010, 11, 11))
        )

    def test_saldo_registrado_en_fecha_antigua_modifica_saldos_de_fechas_posteriores(self):
        Saldo.registrar(self.cuenta, date(2010, 11, 15), 20)
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 30)
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta, fecha=date(2010, 11, 15)).importe,
            50
        )

    def test_segundo_registro_en_fecha_antigua_modifica_saldos_de_fechas_posteriores(self):
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 30)
        Saldo.registrar(self.cuenta, date(2010, 11, 15), 20)
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 40)
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta, fecha=date(2010, 11, 11)).importe,
            70
        )
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta, fecha=date(2010, 11, 15)).importe,
            90
        )

    @patch('diario.models.Saldo._actualizar_posteriores')
    def test_llama_a_actualizar_posteriores(self, mock_actualizar_posteriores):
        Saldo.registrar(self.cuenta, date(2010, 11, 11), 30)
        mock_actualizar_posteriores.assert_called_once_with(
            self.cuenta, date(2010, 11, 11), 30)


class TestSaldoMetodoEliminar(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta normal', 'cn')

    def test_elimina_saldo(self):
        saldo = Saldo.registrar(self.cuenta, date(2010, 11, 11), 100)
        saldo.eliminar()
        self.assertEqual(saldo.cantidad(), 0)
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.tomar(cuenta=saldo.cuenta, fecha=saldo.fecha)

    def test_modifica_saldos_posteriores(self):
        saldo = Saldo.registrar(self.cuenta, date(2010, 11, 11), 100)
        saldo_post = Saldo.registrar(self.cuenta, date(2010, 11, 15), 50)
        saldo.eliminar()
        saldo_post.refresh_from_db()
        self.assertEqual(saldo_post.importe, 50)

    @patch('diario.models.Saldo._actualizar_posteriores')
    def test_llama_a_actualizar_posteriores_con_importe_en_negativo(self, mock_actualizar_posteriores):
        saldo = Saldo.crear(
            cuenta=self.cuenta, fecha=date(2010, 11, 11), importe=100)
        saldo.eliminar()
        mock_actualizar_posteriores.assert_called_once_with(
            self.cuenta, date(2010, 11, 11), -100)


class TestSaldoMetodoActualizarPosteriores(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta normal', 'cn')

    def test_suma_importe_a_saldos_de_cuenta_posteriores_a_fecha_del_saldo(self):
        saldo2 = Saldo.crear(
            cuenta=self.cuenta, fecha=date(2011, 12, 15), importe=150)
        saldo3 = Saldo.crear(
            cuenta=self.cuenta, fecha=date(2012, 5, 6), importe=200)

        Saldo._actualizar_posteriores(self.cuenta, date(2010, 11, 11), 100)
        saldo2.refresh_from_db(fields=['importe'])
        saldo3.refresh_from_db(fields=['importe'])

        self.assertEqual(saldo2.importe, 250)
        self.assertEqual(saldo3.importe, 300)

    def test_no_suma_importe_a_saldos_posteriores_de_otras_cuentas(self):
        cuenta2 = Cuenta.crear('otra cuenta', 'oc')
        saldo2 = Saldo.crear(
            cuenta=cuenta2, fecha=date(2011, 12, 15), importe=200)

        Saldo._actualizar_posteriores(self.cuenta, date(2010, 11, 11), 100)
        saldo2.refresh_from_db(fields=['importe'])

        self.assertEqual(saldo2.importe, 200)

    def test_no_suma_importe_a_saldos_anteriores_de_la_cuenta(self):
        saldo2 = Saldo.crear(
            cuenta=self.cuenta, fecha=date(2010, 11, 10), importe=200)

        Saldo._actualizar_posteriores(self.cuenta, date(2010, 11, 11), 100)
        saldo2.refresh_from_db(fields=['importe'])

        self.assertEqual(saldo2.importe, 200)
