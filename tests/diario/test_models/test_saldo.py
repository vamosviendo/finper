from datetime import date, timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento, Saldo


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


class TestSaldoTomarDeFecha(TestCase):

    def setUp(self):
        self.cuenta1 = Cuenta.crear(
            'cuenta 1', 'c1', fecha_creacion=date(2020, 1, 1))
        self.cuenta2 = Cuenta.crear(
            'cuenta 2', 'c2', fecha_creacion=date(2020, 1, 1))
        Movimiento.crear('mov', 50, self.cuenta1, fecha=date(2020, 1, 2))
        self.mov = Movimiento.crear(
            'otro', 100, self.cuenta1, fecha=date(2020, 1, 2))

    @patch('diario.models.saldo.MiModel.tomar')
    def test_busca_saldo_del_ultimo_movimiento_de_la_cuenta_en_la_fecha(self, mock_tomar):
        Saldo.tomar_de_fecha(cuenta=self.cuenta1, fecha=date(2020, 1, 2))
        mock_tomar.assert_called_once_with(cuenta=self.cuenta1, movimiento=self.mov)

    def test_si_no_hay_movimiento_de_la_cuenta_en_la_fecha_devuelve_ultimo_saldo_anterior(self):
        Movimiento.crear(
            'de otra cuenta', 30, self.cuenta2, fecha=date(2020, 1, 3))
        self.assertEqual(
            Saldo.tomar_de_fecha(cuenta=self.cuenta1, fecha=date(2020, 1, 3)),
            Saldo.tomar_de_fecha(cuenta=self.cuenta1, fecha=date(2020, 1, 2))
        )

    def test_si_no_hay_ningun_movimiento_en_la_fecha_devuelve_saldo_de_ultimo_movimiento_anterior_a_esa_fecha(self):
        Movimiento.crear(
            'de otra cuenta', 30, self.cuenta2, fecha=date(2020, 1, 3))
        self.assertEqual(
            Saldo.tomar_de_fecha(cuenta=self.cuenta1, fecha=date(2020, 1, 4)),
            Saldo.tomar_de_fecha(cuenta=self.cuenta1, fecha=date(2020, 1, 3))
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
            'cuenta 1', 'c1', fecha_creacion=self.fecha)
        self.cuenta2 = Cuenta.crear(
            'cuenta 2', 'c2', fecha_creacion=self.fecha)

    @patch('diario.models.Saldo.crear')
    def test_con_salida_False_crea_saldo_para_cta_entrada(self, mock_crear):
        mov = Movimiento.crear('mov', 100, self.cuenta1, fecha=self.fecha)
        mock_crear.assert_called_once_with(
            cuenta=self.cuenta1,
            importe=100,
            movimiento=mov
        )

    @patch('diario.models.Saldo.crear')
    def test_con_salida_True_crea_saldo_para_cta_salida(self, mock_crear):
        mov = Movimiento.crear('mov', 100, None, self.cuenta2, fecha=self.fecha)
        mock_crear.assert_called_once_with(
            cuenta=self.cuenta2,
            importe=-100,
            movimiento=mov
        )

    def test_importe_de_saldo_creado_para_cta_entrada_es_igual_a_suma_del_importe_del_movimiento_y_el_ultimo_saldo_anterior_de_la_cuenta(self):
        Movimiento.crear('mov', 100, self.cuenta1, fecha=self.fecha)
        with patch('diario.models.Saldo.crear') as mock_crear:
            mov = Movimiento.crear('mov', 70, self.cuenta1, fecha=self.fecha+timedelta(1))

            mock_crear.assert_called_once_with(
                cuenta=self.cuenta1,
                importe=100+70,
                movimiento=mov
            )

    def test_importe_de_saldo_creado_no_suma_importe_de_saldo_correspondiente_a_movimiento_posterior_existente(self):
        Movimiento.crear('mov', 100, self.cuenta1, fecha=self.fecha+timedelta(1))

        with patch('diario.models.Saldo.crear') as mock_crear:
            mov = Movimiento.crear('mov', 70, self.cuenta1, fecha=self.fecha)

            mock_crear.assert_called_once_with(
                cuenta=self.cuenta1,
                importe=0+70,
                movimiento=mov
            )


    def test_importe_de_saldo_creado_para_cta_salida_es_igual_al_ultimo_saldo_anterior_de_la_cuenta_menos_el_importe_del_movimiento(self):
        Movimiento.crear('mov', 100, self.cuenta2, fecha=self.fecha)
        with patch('diario.models.Saldo.crear') as mock_crear:
            mov = Movimiento.crear('mov', 70, None, self.cuenta2, fecha=self.fecha + timedelta(1))

            mock_crear.assert_called_once_with(
                cuenta=self.cuenta2,
                importe=100 - 70,
                movimiento=mov
            )

    @patch('diario.models.Saldo._actualizar_posteriores')
    def test_llama_a_actualizar_posteriores_con_cta_entrada(self, mock_actualizar_posteriores):
        mov = Movimiento.crear('mov', 100, self.cuenta1, fecha=self.fecha)
        mock_actualizar_posteriores.assert_called_once_with(
            self.cuenta1, mov, 100)

    @patch('diario.models.Saldo._actualizar_posteriores')
    def test_llama_a_actualizar_posteriores_con_cta_salida(self, mock_actualizar_posteriores):
        mov = Movimiento.crear('mov', 100, None, self.cuenta2, fecha=self.fecha)
        mock_actualizar_posteriores.assert_called_once_with(
            self.cuenta2, mov, -100)

    def test_integrativo_actualiza_saldos_posteriores_de_cta_entrada(self):
        mov_post = Movimiento.crear(
            'mov posterior', 70, self.cuenta1, fecha=self.fecha+timedelta(2))
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov_post).importe,
            70
        )

        Movimiento.crear('mov anterior', 100, self.cuenta1, fecha=self.fecha)

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

        Movimiento.crear('mov_anterior', 100, None, self.cuenta2, fecha=self.fecha)

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta2, movimiento=mov_post).importe,
            70-100
        )

    def test_devuelve_saldo_generado(self):
        mov = Movimiento.crear('mov', 100, self.cuenta1, fecha=self.fecha)
        mov.saldo_set.first().eliminar()

        self.assertEqual(
            Saldo.generar(mov, salida=False),
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=mov),
        )

    def test_devuelve_None_si_no_genera_saldo(self):
        mov = Movimiento.crear('mov', 100, self.cuenta1, fecha=self.fecha)
        mov.saldo_set.first().eliminar()

        self.assertIsNone(Saldo.generar(mov, salida=True))


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
    def test_llama_a_actualizar_posteriores_con_negativo_de_diferencia_entre_saldo_eliminado_y_ultimo_anterior(self, mock_actualizar_posteriores):
        saldo2 = Movimiento.crear('mov2', 50, self.cuenta, fecha=date(2010, 11, 15)).saldo_set.first()
        mock_actualizar_posteriores.reset_mock()
        saldo2.eliminar()
        mock_actualizar_posteriores.assert_called_once_with(
            saldo2.cuenta, saldo2.movimiento, -(saldo2.importe-self.saldo.importe)
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
