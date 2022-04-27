from datetime import date, timedelta
from unittest.mock import patch, call

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento, Saldo


class TestSaldoBasic(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta normal', 'cn', fecha_creacion=date(2010, 11, 11))

    def test_no_admite_mas_de_un_saldo_por_cuenta_en_cada_movimiento(self):
        mov = Movimiento.crear('mov', 5, self.cuenta, fecha=date(2010, 11, 11))
        # Saldo.crear(cuenta=self.cuenta, fecha=date(2010, 11, 11), importe=10)

        saldo = Saldo()
        saldo.cuenta = self.cuenta
        saldo.movimiento = mov
        saldo.importe = 15

        with self.assertRaises(ValidationError):
            saldo.full_clean()

    def test_saldos_se_ordenan_por_movimiento(self):
        mov1 = Movimiento.crear('mov 1', 10, self.cuenta, fecha=date(2010, 11, 20))
        mov2 = Movimiento.crear('mov 2', 20, self.cuenta, fecha=date(2010, 11, 12))
        mov3 = Movimiento.crear('mov 3', 30, self.cuenta, fecha=date(2010, 11, 12))
        saldo1 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov1)
        saldo2 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov2)
        saldo3 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov3)

        self.assertEqual(list(Saldo.todes()), [saldo2, saldo3, saldo1])


class TestSaldoTomar(TestCase):

    def setUp(self):
        self.cuenta1 = Cuenta.crear(
            'cuenta 1', 'c1', fecha_creacion=date(2020, 1, 1))
        self.cuenta2 = Cuenta.crear(
            'cuenta 2', 'c2', fecha_creacion=date(2020, 1, 1))

    def test_si_no_encuentra_saldo_de_cuenta_en_movimiento_busca_ultimo_saldo_anterior(self):
        mov1 = Movimiento.crear(
            'mov1', 150, self.cuenta1, fecha=date(2020, 1, 2))
        saldo = mov1.saldo_set.first()
        mov2 = Movimiento.crear('mov2', 50, self.cuenta2, fecha=date(2020, 1, 5))

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov2),
            saldo
        )

    def test_si_no_encuentra_saldo_de_cuenta_en_movimiento_ni_saldos_anteriores_lanza_excepcion(self):
        mov = Movimiento.crear('mov', 50, self.cuenta2, fecha=date(2020, 1, 5))
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov)


class TestSaldoMetodoGenerar(TestCase):

    def setUp(self):
        self.fecha = date(2010, 11, 11)
        self.cuenta1 = Cuenta.crear(
            'cuenta 1', 'c1', fecha_creacion=self.fecha)
        self.cuenta2 = Cuenta.crear(
            'cuenta 2', 'c2', fecha_creacion=self.fecha)
        self.mov = Movimiento.crear(
            concepto='traspaso',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2,
            fecha=self.fecha
        )
        Saldo.objects.get(movimiento=self.mov, cuenta=self.cuenta1).delete()
        Saldo.objects.get(movimiento=self.mov, cuenta=self.cuenta2).delete()

    @patch('diario.models.Saldo.crear')
    def test_con_salida_False_crea_saldo_para_cta_entrada(self, mock_crear):
        Saldo.generar(self.mov, salida=False)
        mock_crear.assert_called_once_with(
            cuenta=self.mov.cta_entrada,
            importe=100,
            movimiento=self.mov
        )

    @patch('diario.models.Saldo.crear')
    def test_con_salida_True_crea_saldo_para_cta_salida(self, mock_crear):
        Saldo.generar(self.mov, salida=True)
        mock_crear.assert_called_once_with(
            cuenta=self.mov.cta_salida,
            importe=-100,
            movimiento=self.mov
        )

    @patch('diario.models.Saldo.crear')
    @patch('django.db.models.QuerySet.last')
    def test_saldo_creado_suma_importe_del_mov_recibido_a_ultimo_saldo_anterior_de_cta_entrada(self, mock_last, mock_crear):
        mock_last.return_value = Movimiento(
            concepto='mock mov',
            importe=100,
            fecha=self.fecha,
            cta_entrada=self.cuenta1
        )
        self.mov.fecha = self.fecha + timedelta(1)
        self.mov.importe = 70
        Saldo.generar(self.mov, salida=False)

        mock_crear.assert_called_once_with(
            cuenta=self.cuenta1,
            importe=170,
            movimiento=self.mov
        )

    @patch('diario.models.Saldo.crear')
    @patch('django.db.models.QuerySet.last')
    def test_saldo_creado_resta_importe_del_mov_recibido_a_ultimo_saldo_anterior_de_cta_salida(self, mock_last, mock_crear):
        mock_last.return_value = Movimiento(
            concepto='mock mov',
            importe=100,
            fecha=self.fecha,
            cta_entrada=self.cuenta2
        )
        self.mov.fecha = self.fecha + timedelta(1)
        self.mov.importe = 70
        Saldo.generar(self.mov, salida=True)

        mock_crear.assert_called_once_with(
            cuenta=self.cuenta2,
            importe=30,
            movimiento=self.mov
        )

    @patch('diario.models.Saldo.crear')
    def test_con_salida_True_y_sin_cuenta_de_salida_no_crea_nada(self, mock_crear):
        self.mov.cta_salida = None
        Saldo.generar(self.mov, salida=True)
        mock_crear.assert_not_called()

    @patch('diario.models.Saldo.crear')
    def test_con_salida_False_y_sin_cuenta_de_entrada_no_crea_nada(self, mock_crear):
        self.mov.cta_entrada = None
        Saldo.generar(self.mov, salida=False)
        mock_crear.assert_not_called()

    @patch('diario.models.Saldo._actualizar_posteriores')
    def test_llama_a_actualizar_posteriores_con_cta_entrada(self, mock_actualizar_posteriores):
        Saldo.generar(self.mov, salida=False)
        mock_actualizar_posteriores.assert_called_once_with(
            self.cuenta1, self.mov, 100)

    @patch('diario.models.Saldo._actualizar_posteriores')
    def test_llama_a_actualizar_posteriores_con_cta_salida(self, mock_actualizar_posteriores):
        Saldo.generar(self.mov, salida=True)
        mock_actualizar_posteriores.assert_called_once_with(
            self.cuenta2, self.mov, -100)

    def test_integrativo_actualiza_saldos_posteriores_de_cta_entrada(self):
        mov_post = Movimiento.crear(
            'mov posterior', 70, self.cuenta1, fecha=self.fecha+timedelta(2))
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov_post).importe,
            70
        )

        Saldo.generar(self.mov, salida=False)

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov_post).importe,
            70+100
        )

    def test_integrativo_actualiza_saldos_posteriores_de_cta_salida(self):
        mov_post = Movimiento.crear(
            'mov posterior', 70, self.cuenta2, fecha=self.fecha+timedelta(2))
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta2, movimiento=mov_post).importe,
            70
        )

        Saldo.generar(self.mov, salida=True)

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta2, movimiento=mov_post).importe,
            70-100
        )

    def test_devuelve_saldo_generado(self):
        self.assertEqual(
            Saldo.generar(self.mov, salida=False),
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov),
        )

    def test_devuelve_None_si_no_genera_saldo(self):
        self.mov.cta_salida = None
        self.assertIsNone(Saldo.generar(self.mov, salida=True))

    def test_genera_saldo_de_cuenta_madre_de_cta_entrada(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3', fecha_creacion=date(2010, 1, 1))
        sc31, sc32 = cuenta3.dividir_entre(
            ['subcuenta 3.1', 'sc31', 0],
            ['subcuenta 3.2', 'sc32'],
            fecha=date(2010, 1, 1)
        )
        mov = Movimiento.crear('mov', 100, sc31, fecha=date(2010, 1, 5))
        self.assertEqual(
            Saldo.tomar(cuenta=cuenta3, movimiento=mov).importe,
            100
        )

    def test_genera_saldo_de_cuenta_madre_de_cta_salida(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3', fecha_creacion=date(2010, 1, 1))
        sc31, sc32 = cuenta3.dividir_entre(
            ['subcuenta 3.1', 'sc31', 0],
            ['subcuenta 3.2', 'sc32'],
            fecha=date(2010, 1, 1)
        )
        mov = Movimiento.crear('mov', 100, None, sc31, fecha=date(2010, 1, 5))
        self.assertEqual(
            Saldo.tomar(cuenta=cuenta3, movimiento=mov).importe,
            -100
        )

    def test_genera_saldo_de_cuenta_abuela_de_cta_entrada(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3', fecha_creacion=date(2010, 1, 1))
        sc31, sc32 = cuenta3.dividir_entre(
            ['subcuenta 3.1', 'sc31', 0],
            ['subcuenta 3.2', 'sc32'],
            fecha=date(2010, 1, 1)
        )
        sc311, sc312 = sc31.dividir_entre(
            ['subcuenta 3.1.1', 'sc311', 0],
            ['subcuenta 3.1.2', 'sc312'],
            fecha=date(2010, 1, 1)
        )
        mov = Movimiento.crear('mov', 100, sc311, fecha=date(2010, 1, 5))
        self.assertEqual(
            Saldo.tomar(cuenta=cuenta3, movimiento=mov).importe,
            100
        )

    def test_genera_saldo_de_cuenta_abuela_de_cta_salida(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3', fecha_creacion=date(2010, 1, 1))
        sc31, sc32 = cuenta3.dividir_entre(
            ['subcuenta 3.1', 'sc31', 0],
            ['subcuenta 3.2', 'sc32'],
            fecha=date(2010, 1, 1)
        )
        sc311, sc312 = sc31.dividir_entre(
            ['subcuenta 3.1.1', 'sc311', 0],
            ['subcuenta 3.1.2', 'sc312'],
            fecha=date(2010, 1, 1)
        )
        mov = Movimiento.crear('mov', 100, None, sc311, fecha=date(2010, 1, 5))
        self.assertEqual(
            Saldo.tomar(cuenta=cuenta3, movimiento=mov).importe,
            -100
        )


class TestSaldoMetodoEliminar(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear(
            'cuenta normal', 'cn', fecha_creacion=date(2010, 11, 11))
        mov = Movimiento.crear('mov', 100, self.cuenta, fecha=date(2010, 11, 11))
        self.saldo = mov.saldo_set.first()

    def test_elimina_saldo(self):
        self.saldo.eliminar()
        self.assertEqual(self.saldo.cantidad(), 0)
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(
                cuenta=self.saldo.cuenta,
                movimiento=self.saldo.movimiento
            )

    def test_modifica_saldos_posteriores(self):
        mov2 = Movimiento.crear('mov2', 50, self.cuenta, fecha=date(2010, 11, 15))
        saldo_post = mov2.saldo_set.first()
        self.assertEqual(saldo_post.importe, 150)

        self.saldo.eliminar()
        saldo_post.refresh_from_db()

        self.assertEqual(saldo_post.importe, 50)

    @patch('diario.models.Saldo._actualizar_posteriores')
    def test_llama_a_actualizar_posteriores_con_importe_en_negativo(self, mock_actualizar_posteriores):
        self.saldo.eliminar()
        mock_actualizar_posteriores.assert_called_once_with(
            self.saldo.cuenta, self.saldo.movimiento, -100)

    @patch('diario.models.Saldo._actualizar_posteriores')
    def test_pasa_importe_en_positivo_si_la_cuenta_es_de_salida_en_movimiento(self, mock_actualizar_posteriores):
        self.saldo.eliminar(salida=True)
        mock_actualizar_posteriores.assert_called_once_with(
            self.saldo.cuenta, self.saldo.movimiento, 100)


class TestSaldoMetodoActualizarPosteriores(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear(
            'cuenta normal', 'cn', fecha_creacion=date(2010, 11, 10))
        mov1 = Movimiento.crear(
            'mov1', 150, self.cuenta, fecha=date(2011, 12, 15))
        mov2 = Movimiento.crear(
            'mov2', 50, self.cuenta, fecha=date(2012, 5, 6))
        self.saldo1 = mov1.saldo_set.first()
        self.saldo2 = mov2.saldo_set.first()

    def test_suma_importe_a_saldos_de_cta_entrada_posteriores_a_fecha_del_saldo(self):

        Movimiento.crear('mov0', 100, self.cuenta, fecha=date(2011, 12, 14))
        self.saldo1.refresh_from_db(fields=['importe'])
        self.saldo2.refresh_from_db(fields=['importe'])

        self.assertEqual(self.saldo1.importe, 250)
        self.assertEqual(self.saldo2.importe, 300)

    def test_resta_importe_a_saldos_de_cta_salida_posteriores_a_fecha_del_saldo(self):

        Movimiento.crear(
            'mov0', 100, None, self.cuenta, fecha=date(2011, 12, 14))
        self.saldo1.refresh_from_db(fields=['importe'])
        self.saldo2.refresh_from_db(fields=['importe'])

        self.assertEqual(self.saldo1.importe, 50)
        self.assertEqual(self.saldo2.importe, 100)

    def test_no_suma_importe_a_saldos_posteriores_de_otras_cuentas(self):
        cuenta2 = Cuenta.crear(
            'otra cuenta', 'oc', fecha_creacion=date(2011, 12, 14))

        Movimiento.crear(
            'mov otra cuenta', 200, cuenta2, fecha=date(2011, 12, 14))
        self.saldo1.refresh_from_db(fields=['importe'])
        self.saldo2.refresh_from_db(fields=['importe'])

        self.assertEqual(self.saldo1.importe, 150)
        self.assertEqual(self.saldo2.importe, 200)

    def test_no_suma_importe_a_saldos_anteriores_de_la_cuenta(self):
        Movimiento.crear(
            'mov posterior', 200, self.cuenta, fecha=date(2012, 5, 7))
        self.saldo1.refresh_from_db(fields=['importe'])
        self.saldo2.refresh_from_db(fields=['importe'])

        self.assertEqual(self.saldo1.importe, 150)
        self.assertEqual(self.saldo2.importe, 200)
