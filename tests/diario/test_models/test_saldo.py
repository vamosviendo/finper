from datetime import date, timedelta
from unittest.mock import patch, ANY, MagicMock

from django.core.exceptions import ValidationError
from django.test import TestCase

from utils.tiempo import Posicion
from diario.models import Cuenta, Movimiento, Saldo
from utils import errors


class TestSaldoBasic(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta normal', 'cn', fecha_creacion=date(2010, 11, 11))

    def test_no_admite_mas_de_un_saldo_por_cuenta_en_cada_movimiento(self):
        mov = Movimiento.crear('mov', 5, self.cuenta, fecha=date(2010, 11, 11))

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

    def test_busca_saldo_anterior_por_fecha_y_orden_dia(self):
        mov1 = Movimiento.crear(
            'mov1', 150, self.cuenta1, fecha=date(2020, 1, 2))
        mov2 = Movimiento.crear(
            'mov2', 3, self.cuenta2, fecha=date(2020, 1, 1))
        saldo = mov2.saldo_set.first()

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta2, movimiento=mov1),
            saldo
        )

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov2)


    def test_si_no_encuentra_saldo_de_cuenta_en_movimiento_ni_saldos_anteriores_lanza_excepcion(self):
        mov = Movimiento.crear('mov', 50, self.cuenta2, fecha=date(2020, 1, 5))
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov)

    def test_si_cuenta_es_acumulativa_devuelve_saldo_cuyo_importe_es_suma_de_importes_de_saldos_de_subcuentas_al_momento_del_movimiento(self):
        sc11, sc12 = self.cuenta1.dividir_entre(
            ['subcuenta 1.1', 'sc11', 0],
            ['subcuenta 1.2', 'sc12'],
            fecha=date(2020, 1, 5)
        )
        Movimiento.crear('mov', 50, sc11, fecha=date(2020, 1, 5))
        mov = Movimiento.crear('mov2', 20, None, sc12, fecha=date(2020, 1, 5))
        self.cuenta1 = self.cuenta1.tomar_de_bd()
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov).importe,
            50-20
        )


class TestSaldoMetodoGenerar(TestCase):
    """ Damos por comprobado que Saldo.generar es *siempre* ejecutado por el
        mismo movimiento que luego identificará al saldo generado, usamos
        Movimiento.crear(importe, cta_entrada, cta_salida) como sinónimo de
        Saldo.generar(cta_entrada/salida, importe, movimiento). Con esto nos
        ahorramos un montón de problemas.
    """

    def setUp(self):
        self.fecha = date(2010, 11, 11)
        self.cuenta1 = Cuenta.crear(
            'cuenta 1', 'c1', fecha_creacion=self.fecha-timedelta(1))
        self.cuenta2 = Cuenta.crear(
            'cuenta 2', 'c2', fecha_creacion=self.fecha-timedelta(1))
        self.mov = Movimiento.crear('mov', 100, self.cuenta1, fecha=self.fecha)
        saldo = Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov)
        saldo.delete()

    @patch('diario.models.Saldo.crear')
    def test_crea_saldo_para_cuenta(self, mock_crear):
        Saldo.generar(self.mov, self.cuenta1)
        mock_crear.assert_called_once_with(
            cuenta=self.cuenta1,
            importe=100,
            movimiento=self.mov
        )

    @patch('diario.models.Saldo.crear')
    def test_con_salida_True_invierte_signo_importe(self, mock_crear):
        Saldo.generar(self.mov, self.cuenta1, salida=True)
        mock_crear.assert_called_once_with(
            cuenta=ANY,
            movimiento=ANY,
            importe=-self.mov.importe
        )

    def test_lanza_error_si_cuenta_no_pertenece_a_movimiento(self):
        with self.assertRaisesMessage(
            errors.ErrorCuentaNoFiguraEnMovimiento,
            'La cuenta "cuenta 2" no pertenece al movimiento "mov"'
        ):
            Saldo.generar(self.mov, self.cuenta2)

    @patch('diario.models.Saldo.crear')
    def test_si_no_recibe_cuenta_y_salida_False_toma_cta_entrada_del_movimiento_como_cuenta(self, mock_crear):
        Saldo.generar(self.mov)
        mock_crear.assert_called_once_with(
            movimiento=ANY,
            importe=ANY,
            cuenta=self.mov.cta_entrada
        )

    def test_si_no_recibe_cuenta_y_salida_True_toma_cta_salida_del_movimiento_como_cuenta(self):
        mov = Movimiento.crear('mov', 100, None, self.cuenta1, fecha=self.fecha)
        saldo = Saldo.objects.get(cuenta=self.cuenta1, movimiento=mov)
        saldo.delete()

        with patch('diario.models.Saldo.crear') as mock_crear:
            Saldo.generar(mov, salida=True)
            mock_crear.assert_called_once_with(
                movimiento=ANY,
                importe=ANY,
                cuenta=mov.cta_salida
            )


    def test_importe_de_saldo_creado_es_igual_a_suma_del_importe_del_movimiento_y_el_ultimo_saldo_anterior_de_la_cuenta(self):
        Movimiento.crear('mov', 70, self.cuenta1, fecha=self.fecha-timedelta(1))
        with patch('diario.models.Saldo.crear') as mock_crear:
            Saldo.generar(self.mov, self.cuenta1)
            mock_crear.assert_called_once_with(
                cuenta=ANY,
                movimiento=ANY,
                importe=70+100
            )

    def test_con_salida_True_resta_importe_al_saldo_anterior_en_vez_de_sumarlo(self):
        Movimiento.crear('mov', 170, self.cuenta1, fecha=self.fecha-timedelta(1))
        with patch('diario.models.Saldo.crear') as mock_crear:
            Saldo.generar(self.mov, self.cuenta1, salida=True)
            mock_crear.assert_called_once_with(
                cuenta=ANY,
                movimiento=ANY,
                importe=170-100
            )

    def test_importe_de_saldo_creado_no_suma_importe_de_saldo_correspondiente_a_movimiento_posterior_preexistente(self):
        Movimiento.crear('mov', 70, self.cuenta1, fecha=self.fecha+timedelta(1))

        with patch('diario.models.Saldo.crear') as mock_crear:
            Saldo.generar(self.mov, self.cuenta1)

            mock_crear.assert_called_once_with(
                cuenta=ANY,
                movimiento=ANY,
                importe=0+100
            )

    @patch('diario.models.Saldo._actualizar_posteriores', autospec=True)
    def test_llama_a_actualizar_posteriores_con_importe_de_movimiento(self, mock_actualizar_posteriores):
        saldo = Saldo.generar(self.mov, self.cuenta1)
        mock_actualizar_posteriores.assert_called_once_with(saldo, 100)

    @patch('diario.models.Saldo._actualizar_posteriores', autospec=True)
    def test_con_salida_true_pasa_saldo_en_negativo_a_actualizar_posteriores(self, mock_actualizar_posteriores):
        Saldo.generar(self.mov, self.cuenta1, salida=True)
        mock_actualizar_posteriores.assert_called_once_with(ANY, -100)

    def test_integrativo_actualiza_saldos_posteriores(self):
        mov_post = Movimiento.crear(
            'mov posterior', 70, self.cuenta1, fecha=self.fecha+timedelta(2))
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov_post).importe,
            70
        )

        Saldo.generar(self.mov, self.cuenta1)
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov_post).importe,
            70+100
        )

    def test_devuelve_saldo_generado(self):
        self.assertEqual(
            Saldo.generar(self.mov, self.cuenta1),
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov),
        )


class TestSaldoMetodoEliminar(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear(
            'cuenta normal', 'cn', fecha_creacion=date(2010, 11, 10))
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

    @patch('diario.models.Cuenta.recalcular_saldos_entre', autospec=True)
    def test_llama_a_recalcular_saldos_de_cuenta_de_saldo_eliminado_desde_fecha_de_saldo_en_adelante(self, mock_recalcular):
        saldo2 = Movimiento.crear('mov2', 50, self.cuenta, fecha=date(2010, 11, 15)).saldo_set.first()
        saldo2.eliminar()
        mock_recalcular.assert_called_once_with(saldo2.cuenta, saldo2.posicion)


class TestSaldoMetodoPosterioresA(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear(
            'cuenta normal', 'cn', fecha_creacion=date(2010, 11, 10))
        mov2 = Movimiento.crear(
            'mov2', 150, self.cuenta, fecha=date(2011, 12, 15))
        mov4 = Movimiento.crear(
            'mov4', 50, self.cuenta, fecha=date(2012, 5, 6))
        mov1 = Movimiento.crear('mov1', 200, self.cuenta, fecha=date(2011, 1, 30))
        mov3 = Movimiento.crear('mov3', 2900, self.cuenta, fecha=date(2012, 5, 6))
        mov3.orden_dia = 0
        mov3.save()
        self.saldo1 = mov1.saldo_set.first()
        self.saldo2 = mov2.saldo_set.first()
        self.saldo3 = mov3.saldo_set.first()
        self.saldo4 = mov4.saldo_set.first()

    def test_incluye_saldos_de_cuenta_posteriores_a_fecha_dada(self):
        posteriores = Saldo.posteriores_a(self.cuenta, Posicion(date(2011, 12, 16)))
        self.assertIn(self.saldo3, posteriores)
        self.assertIn(self.saldo4, posteriores)

    def test_incluye_saldos_de_cuenta_de_la_misma_fecha_y_orden_dia_posterior(self):
        self.assertIn(
            self.saldo4,
            Saldo.posteriores_a(
                self.cuenta,
                Posicion(date(2012, 5, 6), orden_dia=0)
            )
        )

    def test_no_incluye_saldos_de_cuenta_de_fecha_anterior_a_la_dada(self):
        self.assertNotIn(
            self.saldo1,
            Saldo.posteriores_a(self.cuenta, Posicion(date(2011, 12, 9)))
        )

    def test_no_incluye_saldos_de_cuenta_de_la_misma_fecha_y_orden_dia_anterior(self):
        self.assertNotIn(
            self.saldo3,
            Saldo.posteriores_a(
                self.cuenta,
                Posicion(date(2012, 5, 6), orden_dia=1)
            )
        )

    def test_con_inclusive_od_false_no_incluye_saldo_con_la_fecha_y_orden_dia_dados(self):
        self.assertNotIn(
            self.saldo4,
            Saldo.posteriores_a(
                self.cuenta,
                Posicion(date(2012, 5, 6), orden_dia=1),
                inclusive_od=False
            )
        )

    def test_con_inclusive_od_true_incluye_saldo_con_la_fecha_y_orden_dia_dados_si_existe(self):
        self.assertIn(
            self.saldo4,
            Saldo.posteriores_a(
                self.cuenta,
                Posicion(date(2012, 5, 6), orden_dia=1),
                inclusive_od=True
            )
        )


class TestSaldoMetodoAnterioresA(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear(
            'cuenta normal', 'cn', fecha_creacion=date(2010, 11, 10))
        mov2 = Movimiento.crear(
            'mov2', 150, self.cuenta, fecha=date(2011, 12, 15))
        mov4 = Movimiento.crear(
            'mov4', 50, self.cuenta, fecha=date(2012, 5, 6))
        mov1 = Movimiento.crear('mov1', 200, self.cuenta, fecha=date(2011, 1, 30))
        mov3 = Movimiento.crear('mov3', 2900, self.cuenta, fecha=date(2012, 5, 6))
        mov3.orden_dia = 0
        mov3.save()
        self.saldo1 = mov1.saldo_set.first()
        self.saldo2 = mov2.saldo_set.first()
        self.saldo3 = mov3.saldo_set.first()
        self.saldo4 = mov4.saldo_set.first()

    def test_incluye_saldos_de_cuenta_anteriores_a_fecha_dada(self):
        anteriores = Saldo.anteriores_a(
            self.cuenta,
            Posicion(date(2011, 12, 16))
        )
        self.assertIn(self.saldo1, anteriores)
        self.assertIn(self.saldo2, anteriores)

    def test_incluye_saldos_de_cuenta_de_la_misma_fecha_y_orden_dia_anterior(self):
        self.assertIn(
            self.saldo3,
            Saldo.anteriores_a(
                self.cuenta,
                Posicion(date(2012, 5, 6), orden_dia=1)
            )
        )

    def test_no_incluye_saldos_de_cuenta_de_fecha_posterior_a_la_dada(self):
        self.assertNotIn(
            self.saldo3,
            Saldo.anteriores_a(self.cuenta, Posicion(date(2011, 12, 16)))
        )

    def test_no_incluye_saldos_de_cuenta_de_la_misma_fecha_y_orden_dia_posterior(self):
        saldo5 = Movimiento.crear(
            'mov3', 2900, self.cuenta, fecha=date(2012, 5, 6)
        ).saldo_ce()

        self.assertNotIn(
            saldo5,
            Saldo.anteriores_a(
                self.cuenta,
                Posicion(date(2012, 5, 6), orden_dia=1)
            )
        )

    def test_con_inclusive_od_false_no_incluye_saldo_con_la_fecha_y_orden_dia_dados(self):
        self.assertNotIn(
            self.saldo4,
            Saldo.anteriores_a(
                self.cuenta,
                Posicion(date(2012, 5, 6), orden_dia=1),
                inclusive_od=False
            )
        )

    def test_con_inclusive_od_true_incluye_saldo_con_la_fecha_y_orden_dia_dados_si_existe(self):
        self.assertIn(
            self.saldo4,
            Saldo.anteriores_a(
                self.cuenta,
                Posicion(date(2012, 5, 6), orden_dia=1),
                inclusive_od=True
            )
        )


class TestSaldoMetodoActualizarPosteriores(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear(
            'cuenta normal', 'cn', fecha_creacion=date(2010, 11, 10))
        self.mov1 = Movimiento.crear(
            'mov1', 150, self.cuenta, fecha=date(2011, 12, 15))
        self.mov2 = Movimiento.crear(
            'mov2', 50, self.cuenta, fecha=date(2012, 5, 6))
        self.saldo1 = self.mov1.saldo_set.first()
        self.saldo2 = self.mov2.saldo_set.first()

    def test_suma_importe_a_saldos_de_cta_entrada_posteriores_a_fecha_del_saldo(self):

        Movimiento.crear('mov0', 100, self.cuenta, fecha=date(2011, 12, 14))
        self.assertEqual(
            Saldo.objects.get(cuenta=self.cuenta, movimiento=self.mov1).importe,
            250
        )
        self.assertEqual(
            Saldo.objects.get(cuenta=self.cuenta, movimiento=self.mov2).importe,
            300
        )
        self.saldo1.refresh_from_db(fields=['_importe'])
        self.saldo2.refresh_from_db(fields=['_importe'])

        self.assertEqual(self.saldo1.importe, 250)
        self.assertEqual(self.saldo2.importe, 300)

    def test_resta_importe_a_saldos_de_cta_salida_posteriores_a_fecha_del_saldo(self):

        Movimiento.crear(
            'mov0', 100, None, self.cuenta, fecha=date(2011, 12, 14))
        self.saldo1.refresh_from_db(fields=['_importe'])
        self.saldo2.refresh_from_db(fields=['_importe'])

        self.assertEqual(self.saldo1.importe, 50)
        self.assertEqual(self.saldo2.importe, 100)

    def test_no_suma_importe_a_saldos_posteriores_de_otras_cuentas(self):
        cuenta2 = Cuenta.crear(
            'otra cuenta', 'oc', fecha_creacion=date(2011, 12, 14))

        Movimiento.crear(
            'mov otra cuenta', 200, cuenta2, fecha=date(2011, 12, 14))
        self.saldo1.refresh_from_db(fields=['_importe'])
        self.saldo2.refresh_from_db(fields=['_importe'])

        self.assertEqual(self.saldo1.importe, 150)
        self.assertEqual(self.saldo2.importe, 200)

    def test_no_suma_importe_a_saldos_anteriores_de_la_cuenta(self):
        Movimiento.crear(
            'mov posterior', 200, self.cuenta, fecha=date(2012, 5, 7))
        self.saldo1.refresh_from_db(fields=['_importe'])
        self.saldo2.refresh_from_db(fields=['_importe'])

        self.assertEqual(self.saldo1.importe, 150)
        self.assertEqual(self.saldo2.importe, 200)


class TestSaldoMetodoActualizarImporteYAnteriores(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear(
            'cta', 'c', fecha_creacion=date(2010, 11, 11))
        mov1 = Movimiento.crear(
            'mov1', 100, self.cuenta, fecha=date(2010, 11, 13))
        mov2 = Movimiento.crear(
            'mov2', 200, self.cuenta, fecha=date(2010, 11, 14))
        self.saldo1 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov1)
        self.saldo2 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov2)
        self.saldo1.sumar_a_este_y_posteriores(1000)

    def test_suma_importe_a_importe_de_saldo(self):
        self.saldo1.refresh_from_db()
        self.assertEqual(self.saldo1.importe, 1100)

    def test_suma_importe_a_importes_posteriores_a_saldo(self):
        self.saldo2.refresh_from_db()
        self.assertEqual(self.saldo2.importe, 1300)


class TestSaldoMetodoAnterior(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear(
            'cta', 'c', fecha_creacion=date(2010, 11, 11))

    def test_devuelve_ultimo_saldo_anterior_de_la_cuenta_por_fecha(self):
        mov1 = Movimiento.crear(
            'mov1', 100, self.cuenta, fecha=date(2010, 11, 15))
        mov2 = Movimiento.crear(
            'mov2', 200, self.cuenta, fecha=date(2010, 11, 14))
        saldo1 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov1)
        saldo2 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov2)
        self.assertEqual(saldo1.anterior(), saldo2)

    def test_dentro_de_fecha_devuelve_ultimo_saldo_anterior_de_la_cuenta_por_orden_dia(self):
        mov1 = Movimiento.crear(
            'mov1', 100, self.cuenta, fecha=date(2010, 11, 15))
        mov2 = Movimiento.crear(
            'mov2', 200, self.cuenta, fecha=date(2010, 11, 15))
        mov1.orden_dia = 1
        mov2.orden_dia = 0
        mov1.save()
        mov2.save()

        saldo1 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov1)
        saldo2 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov2)

        self.assertEqual(saldo1.anterior(), saldo2)

    def test_si_no_hay_saldos_anteriores_por_fecha_u_orden_dia_devuelve_None(self):
        mov1 = Movimiento.crear(
            'mov1', 100, self.cuenta, fecha=date(2010, 11, 15))
        saldo1 = Saldo.objects.get(cuenta=self.cuenta, movimiento=mov1)

        self.assertIsNone(saldo1.anterior())


class TestSaldoPropertyImporte(TestCase):

    def setUp(self):

        self.cuenta = Cuenta.crear('cuenta', 'c')

    def test_asigna_importe_a_campo__importe(self):
        saldo = Saldo(cuenta=self.cuenta)
        saldo.importe = 150
        self.assertEqual(saldo._importe, 150)

    def test_devuelve_importe_del_saldo(self):
        saldo = Saldo(cuenta=self.cuenta, _importe=123)
        self.assertEqual(saldo.importe, saldo._importe)

    def test_redondea_valor_antes_de_asignarlo_a_campo__importe(self):
        saldo = Saldo(cuenta=self.cuenta, importe=154.588)
        self.assertEqual(saldo._importe, 154.59)


class TestSaldoPropertiesVieneDeEntradaVieneDeSalida(TestCase):

    def setUp(self):
        self.cuenta = Cuenta.crear('cuenta', 'c')
        self.saldo1 = Movimiento.crear('mov1', 5, self.cuenta).saldo_ce()
        self.saldo2 = Movimiento.crear('mov2', 6, None, self.cuenta).saldo_cs()

    def test_vde_devuelve_true_y_vds_false_si_la_cuenta_es_cta_entrada_de_su_movimiento(self):
        self.assertTrue(self.saldo1.viene_de_entrada)
        self.assertFalse(self.saldo1.viene_de_salida)

    def test_vde_devuelve_false_y_vds_true_si_la_cuenta_es_cta_salida_de_su_movimiento(self):
        self.assertTrue(self.saldo2.viene_de_salida)
        self.assertFalse(self.saldo2.viene_de_entrada)