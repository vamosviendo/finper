from datetime import date, timedelta
from unittest.mock import patch, call

from django.core.exceptions import ValidationError

from diario.models import Cuenta, Movimiento, Titular, Saldo
from utils import errors
from utils.helpers_tests import dividir_en_dos_subcuentas

from .test_movimiento import TestModelMovimientoSave


class TestModelMovimientoSaveGeneral(TestModelMovimientoSave):

    @patch('diario.models.movimiento.Saldo.save')
    def test_no_modifica_saldo_en_mov_si_no_se_modifica_importe_ni_cuentas_ni_fecha(self, mock_save):
        self.mov3.concepto = 'Depósito en efectivo'
        self.mov3.save()

        mock_save.assert_not_called()

    def test_integrativo_no_modifica_saldo_en_mov_si_no_se_modifica_importe_ni_cuentas_ni_fecha(self):
        self.mov3.concepto = 'Depósito en efectivo'
        self.mov3.save()

        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov3), 140)
        self.assertEqual(self.cuenta2.saldo_en_mov(self.mov3), -50)

    @patch.object(Movimiento, '_regenerar_contramovimiento')
    def test_en_movimiento_con_contramovimiento_no_regenera_contramovimiento_si_se_modifica_concepto(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.concepto = 'Prastamo'
        movimiento.save()

        mock_regenerar_contramovimiento.assert_not_called()

    @patch.object(Movimiento, '_regenerar_contramovimiento')
    def test_en_movimiento_con_contramovimiento_no_regenera_contramovimiento_si_se_modifica_detalle(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.detalle = 'El titular 1 le presta al titular 2 30 pesotes'
        movimiento.save()

        mock_regenerar_contramovimiento.assert_not_called()

    @patch.object(Movimiento, '_regenerar_contramovimiento')
    def test_en_movimiento_con_contramovimiento_no_regenera_contramovimiento_si_se_modifica_orden_dia(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.orden_dia -= 1
        movimiento.save()

        mock_regenerar_contramovimiento.assert_not_called()

    @patch.object(Movimiento, '_regenerar_contramovimiento', autospec=True)
    def test_en_movimiento_con_contramovimiento_regenera_contramovimiento_si_se_modifica_fecha(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.fecha = date(2020, 2, 23)
        movimiento.save()

        mock_regenerar_contramovimiento.assert_called_once_with(movimiento)

    def test_no_permite_modificar_contramovimientos(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        contramov.concepto = 'Dádiva'
        with self.assertRaisesMessage(
                ValidationError,
                'No se puede modificar movimiento automático'):
            contramov.full_clean()


class TestModelMovimientoSaveModificaImporte(TestModelMovimientoSave):

    @patch('diario.models.movimiento.Saldo.crear')
    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_elimina_saldo_antiguo_y_genera_uno_nuevo_para_cta_entrada_en_movimiento(self, mock_eliminar, mock_crear):
        saldo = Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov1)

        self.mov1.importe = 128
        self.mov1.save()

        mock_eliminar.assert_called_once_with(saldo)
        mock_crear.assert_called_once_with(
            cuenta=self.cuenta1,
            importe=128,
            movimiento=self.mov1
        )

    def test_integrativo_resta_importe_antiguo_y_suma_el_nuevo_a_saldo_de_cta_entrada_en_movimiento(self):
        self.mov1.importe = 128
        self.mov1.save()
        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov1), 125-125+128)

    def test_integrativo_actualiza_saldo_de_cuenta_en_movimiento_y_posteriores(self):
        self.mov1.importe = 110
        self.mov1.save()

        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov1), 110)
        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov2), 75)

    @patch('diario.models.movimiento.Saldo.crear')
    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_elimina_saldo_antiguo_y_genera_uno_nuevo_para_cta_salida_en_movimiento(self, mock_eliminar, mock_crear):
        saldo = Saldo.tomar(cuenta=self.cuenta1, movimiento=self.mov2)

        self.mov2.importe = 37
        self.mov2.save()

        mock_eliminar.assert_called_once_with(saldo)
        mock_crear.assert_called_once_with(
            cuenta=self.cuenta1,
            importe=125-37,
            movimiento=self.mov2,
        )

    def test_integrativo_suma_importe_antiguo_y_resta_el_nuevo_de_cta_salida_en_movimiento(self):
        self.mov2.importe = 37
        self.mov2.save()

        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov2), 90+35-37)

    @patch('diario.models.movimiento.Saldo.crear')
    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_en_mov_de_traspaso_elimina_saldo_antiguo_y_genera_nuevo_para_cta_entrada_y_cta_salida(
            self, mock_eliminar, mock_crear):
        saldo_ce = Saldo.tomar(cuenta=self.cuenta1, movimiento=self.mov3)
        saldo_cs = Saldo.tomar(cuenta=self.cuenta2, movimiento=self.mov3)

        self.mov3.importe = 60
        self.mov3.save()

        self.assertEqual(
            mock_eliminar.call_args_list,
            [call(saldo_ce), call(saldo_cs)]
        )
        self.assertEqual(
            mock_crear.call_args_list,
            [
                call(cuenta=self.cuenta1, importe=90+60, movimiento=self.mov3),
                call(cuenta=self.cuenta2, importe=0-60, movimiento=self.mov3),
            ]
        )

    @patch.object(Movimiento, '_regenerar_contramovimiento', autospec=True)
    def test_en_movimientos_con_contramovimiento_elimina_contramovimiento_para_volver_a_generarlo(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.importe = 45
        movimiento.save()

        mock_regenerar_contramovimiento.assert_called_once_with(movimiento)

    def test_en_mov_traspaso_con_contramov_cambia_importe_contramov(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.importe = 45
        movimiento.save()

        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        self.assertEqual(contramov.importe, 45)

    def test_en_mov_traspaso_con_contramov_cambia_saldo_en_las_cuentas_del_contramov(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        cta_deudora = contramov.cta_salida
        cta_acreedora = contramov.cta_entrada

        movimiento.importe = 45
        movimiento.save()

        self.assertEqual(cta_deudora.saldo, -45)
        self.assertEqual(cta_acreedora.saldo, 45)


class TestModelMovimientoSaveModificaCuentas(TestModelMovimientoSave):

    def test_cambiar_cta_entrada_elimina_saldo_de_cuenta_antigua_en_movimiento(self):
        saldo_ce = self.mov1.saldo_ce()
        self.mov1.cta_entrada = self.cuenta2

        self.mov1.save()
        saldo_ce.refresh_from_db(fields=['cuenta'])

        self.assertEqual(saldo_ce.cuenta_id, self.cuenta2.id)


    @patch('diario.models.movimiento.Saldo.generar')
    def test_cambiar_cta_entrada_genera_saldo_de_cuenta_nueva_en_movimiento(self, mock_generar):
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()

        mock_generar.assert_called_once_with(
            self.mov1, salida=False
        )

    def test_integrativo_cambiar_cta_entrada_genera_saldo_de_cuenta_nueva_en_movimiento(self):
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(self.cuenta2.saldo_en_mov(self.mov1), 0+125)

    def test_cambiar_cta_salida_elimina_saldo_de_cuenta_antigua_en_movimiento(self):
        saldo_cs = self.mov2.saldo_cs()
        self.mov2.cta_salida = self.cuenta2

        self.mov2.save()
        saldo_cs.refresh_from_db(fields=['cuenta'])

        self.assertEqual(saldo_cs.cuenta_id, self.cuenta2.id)


    @patch('diario.models.movimiento.Saldo.generar')
    def test_cambiar_cta_salida_genera_saldo_de_cuenta_nueva_en_movimiento(self, mock_generar):
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()

        mock_generar.assert_called_once_with(
            self.mov2, salida=True
        )

    def test_integrativo_cambiar_cta_salida_genera_saldo_de_cuenta_nueva_en_movimiento(self):
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2).importe,
            0 - 35
        )

    def test_modificar_cta_entrada_funciona_en_movimientos_de_traspaso(self):
        cuenta3 = Cuenta.crear('Cuenta 3', 'c3')
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            50
        )

    def test_modificar_cta_salida_funciona_en_movimientos_de_traspaso(self):
        cuenta3 = Cuenta.crear('Cuenta 3', 'c3')
        self.mov3.cta_salida = cuenta3
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            -50
        )

    def test_modificar_ambas_cuentas_funciona_en_movimientos_de_traspaso(self):
        cuenta3 = Cuenta.crear('cuenta 3', 'c3')
        cuenta4 = Cuenta.crear('cuenta 4', 'c4')

        self.mov3.cta_entrada = cuenta3
        self.mov3.cta_salida = cuenta4
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            50
        )
        self.assertEqual(cuenta4.saldo_set.count(), 1)
        self.assertEqual(
            cuenta4.saldo_set.get(movimiento=self.mov3).importe,
            -50
        )

    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    @patch('diario.models.movimiento.Saldo.crear')
    def test_intercambiar_cuentas_resta_importe_x2_de_saldo_en_fecha_de_cta_entrada_y_lo_suma_a_saldo_en_fecha_de_cta_salida(
            self, mock_crear, mock_eliminar):
        self.mov3.cta_salida = self.cuenta1
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.save()

        self.assertEqual(
            mock_eliminar.call_args_list,
            [
                call(self.cuenta1.saldo_set.get(movimiento=self.mov3)),
                call(self.cuenta2.saldo_set.get(movimiento=self.mov3))
            ]
        )

        self.assertEqual(
            mock_crear.call_args_list,
            [
                call(
                    cuenta=self.cuenta2,
                    importe=0+self.mov3.importe,
                    movimiento=self.mov3
                ),
                call(
                    cuenta=self.cuenta1,
                    importe=90-self.mov3.importe,
                    movimiento=self.mov3
                )
            ]
        )

    def test_integrativo_intercambiar_cuentas_resta_importe_x2_de_saldo_en_movimiento_de_cta_entrada_y_lo_suma_a_saldo_en_movimiento_de_cta_salida(
            self):
        self.mov3.cta_salida = self.cuenta1
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 50 * 2
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 50 * 2
        )

    def test_cuenta_de_salida_pasa_a_ser_de_entrada(self):
        """ Suma dos veces importe a saldo de vieja cta_salida (ahora
            cta_entrada) al momento del movimiento"""
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90 + 35 * 2
        )

    def test_cuenta_de_entrada_pasa_a_ser_de_salida(self):
        """ Resta dos veces importe a saldo de vieja cta_entrada (ahora
            cta_salida) al momento del movimiento"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125 - 125 * 2
        )

    def test_cuenta_de_salida_pasa_a_ser_de_entrada_y_cuenta_nueva_de_salida(self):
        """ Suma dos veces importe a saldo de vieja cta_salida (ahora
            cta_entrada) al momento del movimiento.
            Desaparece saldo de nueva cta_salida al momento del movimiento"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 50 * 2
        )
        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            -50
        )

    def test_cuenta_de_entrada_pasa_a_ser_de_salida_y_cuenta_nueva_de_entrada(self):
        """ Desaparece saldo de vieja cta_entrada (ahora cta_salida) al momento
            del movimiento.
            Suma importe a saldo de nueva cta_entrada al momento del
            movimiento"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 50 * 2
        )
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            50
        )

    def test_cuenta_de_salida_desaparece(self):
        """ Suma importe a saldo de cta_salida retirada al momento del
            movimiento"""
        self.mov3.cta_salida = None
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

    def test_cuenta_de_entrada_desaparece(self):
        """ Desaparece saldo de cuenta de entrada en movimiento"""
        self.mov3.cta_entrada = None
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida(self):
        """ Desaparece saldo de cta_salida retirada al momento del movimiento.
            Resta dos veces importe de saldo de vieja cta_entrada (ahora
            cta_salida) al momento del movimiento."""
        saldo = self.mov3.saldo_ce()
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None

        self.mov3.save()
        saldo.refresh_from_db(fields=['cuenta', '_importe'])

        self.assertEqual(saldo.cuenta_id, self.cuenta1.id)
        self.assertEqual(saldo.importe, 140 - 50 * 2)

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada(self):
        """ Desaparece saldo de cta_entrada retirada al momento del movimiento.
            Suma dos veces importe a saldo de vieja cta_salida (ahora
            cta_entrada) al momento del movimiento"""
        saldo = self.mov3.saldo_cs()
        self.mov3.cta_entrada = self.mov3.cta_salida  # self.cuenta2
        self.mov3.cta_salida = None

        self.mov3.save()
        saldo.refresh_from_db(fields=['cuenta', '_importe'])

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

        self.assertEqual(saldo.cuenta_id, self.cuenta2.id)
        self.assertEqual(saldo.importe, -50 + 50 * 2)

    def test_aparece_cuenta_de_salida(self):
        """ Aparece saldo de nueva cta_salida al momento del movimiento """
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov1).importe,
            0 - 125
        )

    def test_aparece_cuenta_de_entrada(self):
        """ Aparece saldo de nueva cta_salida al momento del movimiento """
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.save()

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2).importe,
            0 + 35
        )

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada(self):
        """ Resta dos veces importe de vieja cta_entrada (ahora cta_salida) al
            momento del movimiento
            Aparece saldo de nueva cta_entrada al momento del movimiento"""
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125 - 125 * 2
        )
        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov1).importe,
            0 + 125
        )

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada) al
            momento del movimiento
            Aparece saldo de nueva cta_salida al momento del movimiento """
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2).importe,
            0 - 35
        )

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90 + 35 * 2
        )

    def test_desaparece_cta_entrada_y_aparece_cta_de_salida(self):
        """ Desaparece saldo de cta_entrada retirada al momento del movimiento.
            Aparece saldo de cta_salida agregada al momento del movimiento"""
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov1)

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov1).importe,
            0 - 125
        )

    def test_desaparece_cta_salida_y_aparece_cta_de_entrada(self):
        """ Desaparece saldo de cta_salida retirada al momento del movimiento.
            Aparece saldo de cta_entrada agregada al momento del movimiento"""
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.cta_salida = None
        self.mov2.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov2)

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2).importe,
            0 + 35
        )

    @patch.object(Movimiento, '_regenerar_contramovimiento', autospec=True)
    def test_cambiar_cta_entrada_por_cta_otro_titular_en_movimientos_con_contramovimiento_regenera_contramovimiento(
            self, mock_regenerar_contramovimiento):
        titular = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta4 = Cuenta.crear(
            nombre='Cuenta tit3', slug='ct3', titular=titular)
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.cta_entrada = cuenta4
        movimiento.save()

        mock_regenerar_contramovimiento.assert_called_once_with(movimiento)

    def test_cambiar_cta_entrada_por_cta_otro_titular_en_movimiento_de_traspaso_con_contramovimiento_modifica_contramovimiento(
            self):
        titular = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta4 = Cuenta.crear(
            nombre='Cuenta tit3', slug='ct3', titular=titular)
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        cta_deudora = contramov.cta_salida

        movimiento.cta_entrada = cuenta4
        movimiento.save()

        contramov = Movimiento.tomar(id=movimiento.id_contramov)

        self.assertNotEqual(contramov.cta_salida.id, cta_deudora.id)
        self.assertEqual(contramov.cta_salida.slug, '_tit3-default')

    @patch.object(Movimiento, '_regenerar_contramovimiento', autospec=True)
    def test_cambiar_cta_salida_por_cta_otro_titular_en_movimientos_con_contramovimiento_regenera_contramovimiento(
            self, mock_regenerar_contramovimiento):
        titular = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta4 = Cuenta.crear(
            nombre='Cuenta tit3', slug='ct3', titular=titular)
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.cta_salida = cuenta4
        movimiento.save()

        mock_regenerar_contramovimiento.assert_called_once_with(movimiento)

    def test_cambiar_cta_salida_por_cta_otro_titular_en_movimiento_de_traspaso_con_contramovimiento_modifica_contramovimiento(
            self):
        titular = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta4 = Cuenta.crear(
            nombre='Cuenta tit3', slug='ct3', titular=titular)
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        cta_deudora = contramov.cta_salida

        movimiento.cta_salida = cuenta4
        movimiento.save()

        contramov = Movimiento.tomar(id=movimiento.id_contramov)

        self.assertNotEqual(contramov.cta_entrada.id, cta_deudora.id)
        self.assertEqual(contramov.cta_entrada.slug, '_tit3-tit2')

    @patch.object(Movimiento, '_crear_movimiento_credito', autospec=True)
    def test_cambiar_cta_entrada_por_cta_otro_titular_en_movimiento_de_traspaso_sin_contramovimiento_genera_contramovimiento(
            self, mock_crear_movimiento_credito):
        self.mov3.cta_entrada = self.cuenta3
        self.mov3.save()

        mock_crear_movimiento_credito.assert_called_once_with(self.mov3)

    @patch.object(Movimiento, '_crear_movimiento_credito', autospec=True)
    def test_cambiar_cta_salida_por_cta_otro_titular_en_movimiento_de_traspaso_sin_contramovimiento_genera_contramovimiento(
            self, mock_crear_movimiento_credito):
        self.mov3.cta_salida = self.cuenta3
        self.mov3.save()

        mock_crear_movimiento_credito.assert_called_once_with(self.mov3)

    @patch.object(Movimiento, '_eliminar_contramovimiento', autospec=True)
    def test_cambiar_cta_entrada_por_cta_mismo_titular_de_cta_salida_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento(
            self, mock_eliminar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.cta_entrada = self.cuenta2
        movimiento.save()

        mock_eliminar_contramovimiento.assert_called_once_with(movimiento)

    def test_cambiar_cta_entrada_por_cta_mismo_titular_de_cta_salida_en_movimiento_de_traspaso_con_contramovimiento_no_regenera_contramovimiento_destruido(
            self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        with patch.object(Movimiento, '_crear_movimiento_credito') \
                as mock_crear_movimiento_credito:
            movimiento.cta_entrada = self.cuenta2
            movimiento.save()

            mock_crear_movimiento_credito.assert_not_called()

    def test_cambiar_cta_salida_por_cta_mismo_titular_de_cta_entrada_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento(
            self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta3)
        id_contramovimiento = movimiento.id_contramov

        movimiento.cta_salida = self.cuenta2
        movimiento.save()

        with self.assertRaises(Movimiento.DoesNotExist):
            Movimiento.tomar(id=id_contramovimiento)

    def test_cambiar_cta_salida_por_cta_mismo_titular_de_cta_entrada_en_movimiento_de_traspaso_con_contramovimiento_no_regenera_contramovimiento_destruido(
            self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta3)

        with patch.object(Movimiento, '_crear_movimiento_credito') \
                as mock_crear_movimiento_credito:
            movimiento.cta_salida = self.cuenta2
            movimiento.save()

            mock_crear_movimiento_credito.assert_not_called()


class TestModelMovimientoSaveModificaImporteYCuentas(TestModelMovimientoSave):

    def test_cambia_cuenta_de_entrada_con_nuevo_importe(self):
        """ Desaparece saldo de cta_entrada vieja al momento del movimiento
            Aparece saldo con nuevo importe de cta_entrada nueva al momento del
            movimiento"""
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 128
        self.mov1.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov1)

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov1).importe,
            0 + 128
        )

    def test_cambia_cuenta_de_salida_con_nuevo_importe(self):
        """ Desaparece saldo de cta_salida vieja al momento del movimiento
            Aparece saldo con nuevo importe de cta_salida nueva al momento del
            movimiento """
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov2.cta_salida = self.cuenta2
        self.mov2.importe = 63
        self.mov2.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov2)

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2).importe,
            0 - 63
        )

    def test_cambia_cuenta_de_entrada_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Desaparece saldo de cta_entrada vieja al momento del movimiento
            Aparece saldo con nuevo importe de cta_entrada nueva al momento del
            movimiento
            Suma importe viejo y resta importe nuevo a cta_salida """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_entrada = cuenta3
        self.mov3.importe = 56
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            0 + 56
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 50 - 56
        )

    def test_cambia_cuenta_de_salida_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Desaparece saldo de cta_salida vieja al momento del movimiento
            Aparece saldo con nuevo importe de cta_salida nueva al momento del
            movimiento
            Resta importe viejo y suma importe nuevo a cta_entrada """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 56
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            0 - 56
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 50 + 56
        )

    def test_cambian_ambas_cuentas_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Desaparece saldo de cta_entrada vieja al momento del movimiento
            Desaparece saldo de cta_salida vieja al momento del movimiento
            Aparece saldo con nuevo importe de cta_entrada nueva al momento del
            movimiento
            Aparece saldo con nuevo importe de cta_salida nueva al momento del
            movimiento"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        cuenta4 = Cuenta.crear('Colchón', 'ch')

        self.mov3.cta_entrada = cuenta3
        self.mov3.cta_salida = cuenta4
        self.mov3.importe = 56
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            0 + 56
        )
        self.assertEqual(cuenta4.saldo_set.count(), 1)
        self.assertEqual(
            cuenta4.saldo_set.get(movimiento=self.mov3).importe,
            0 - 56
        )

    def test_se_intercambian_cuentas_de_entrada_y_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo de saldo de cta_entrada vieja
                (ahora cta_salida) al momento del movimiento
            Suma importe viejo e importe nuevo a saldo de cta_salida vieja
                (ahora cta_entrada) al momento del movimiento"""
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.cta_salida = self.cuenta1
        self.mov3.importe = 456
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 50 - 456
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 50 + 456
        )

    def test_cta_entrada_pasa_a_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a saldo de cta_entrada vieja
                (ahora cta_salida) al momento del movimiento"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.importe = 128
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125 - 125 - 128
        )

    def test_cta_salida_pasa_a_entrada_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada) al momento del movimiento"""
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.importe = 128
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90 + 35 + 128
        )

    def test_cta_salida_pasa_entrada_y_cta_salida_nueva_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a saldo de cta_salida vieja
                (ahora cta_entrada) al momento del movimiento
            Desaparece saldo de cta_entrada vieja al momento del movimiento
            Aparece saldo con nuevo importe de cta_salida nueva al momento del
            movimiento"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 252
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 50 + 252
        )
        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            0 - 252
        )

    def test_cta_entrada_pasa_salida_y_cta_entrada_nueva_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a saldo de cta_entrada vieja
                (ahora cta_entrada) al momento del movimiento
            Desaparece saldo de cta_salida vieja al momento del movimiento
            Aparece saldo con nuevo importe de cta_entrada nueva al momento del
            movimiento """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta3
        self.mov3.importe = 165
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 50 - 165
        )
        self.assertEqual(cuenta3.saldo_set.count(), 1)
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=self.mov3).importe,
            0 + 165
        )

    def test_cuenta_de_salida_desaparece_con_nuevo_importe(self):
        """ Desaparece saldo de cta_salida vieja al momento del movimiento
            Resta importe viejo y suma importe nuevo a saldo de cta_entrada al
            momento del movimiento"""
        self.mov3.cta_salida = None
        self.mov3.importe = 234
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 50 + 234
        )

    def test_cuenta_de_entrada_desaparece_con_nuevo_importe(self):
        """ Desaparece saldo de cta_entrada vieja al momento del movimiento
            Suma importe viejo y resta importe nuevo a saldo de cta_salida al
            momento del movimiento"""
        self.mov3.cta_entrada = None
        self.mov3.importe = 234
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 50 - 234
        )

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida_con_nuevo_importe(
            self):
        """ Resta importe viejo e importe nuevo a saldo de vieja cta_entrada
            (ahora cta_salida) al momento del movimiento
            Desaparece saldo de cta_salida vieja al momento del movimiento """
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.importe = 350
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 50 - 350
        )

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada_con_nuevo_importe(
            self):
        """ Suma importe viejo e importe nuevo a saldo de vieja cta_salida
            (ahora cta_entrada) al momento del movimiento.
            Desaparece saldo de cta_entrada vieja al momento del movimiento """
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.importe = 354
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 50 + 354
        )

    def test_aparece_cuenta_de_salida_con_nuevo_importe(self):
        """ Resta importe viejo y suma importe nuevo a saldo de cta_entrada al
            momento del movimiento
            Aparece saldo con nuevo importe de cta_salida nueva al momento del
            movimiento"""
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 255
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125 - 125 + 255
        )
        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov1).importe,
            0 - 255
        )

    def test_aparece_cuenta_de_entrada_con_nuevo_importe(self):
        """ Suma importe viejo y resta importe nuevo a saldo de cta_salida al
            momento del movimiento
            Aparece saldo con nuevo importe de cta_entrada nueva al momento del
            movimiento"""
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.importe = 446
        self.mov2.save()

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2).importe,
            0 + 446
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90 + 35 - 446
        )

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada_con_nuevo_importe(
            self):
        """ Resta importe viejo e importe nuevo de saldo de antigua cta_entrada
            (ahora cta_salida) al momento del movimiento
            Aparece saldo con nuevo importe de cta_entrada nueva al momento del
            movimiento"""
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 556
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125 - 125 - 556
        )
        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov1).importe,
            0 + 556
        )

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida_con_nuevo_importe(
            self):
        """ Suma importe viejo e importe nuevo a saldo de antigua cta_salida
            (ahora cta_entrada) al momento del movimiento
            Aparece saldo con nuevo importe de cta_salida nueva al momento del
            movimiento """
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta2
        self.mov2.importe = 445
        self.mov2.save()

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2).importe,
            0 - 445
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90 + 35 + 445
        )

    def test_desaparece_cta_entrada_y_aparece_otra_cta_de_salida_con_nuevo_importe(self):
        """ Desaparece saldo de cta_entrada retirada al momento del movimiento
            Aparece saldo con nuevo importe de cta_salida nueva al momento del
            movimiento """
        cant_saldos = self.cuenta2.saldo_set.count()
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 565
        self.mov1.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov1)
        self.assertEqual(self.cuenta2.saldo_set.count(), cant_saldos+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov1).importe,
            0 - 565
        )

    def test_desaparece_cta_salida_y_aparece_otra_cta_de_entrada_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida retirada
            Suma importe nuevo a cta_entrada agregada """
        cant_movs = self.cuenta2.saldo_set.count()
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.cta_salida = None
        self.mov2.importe = 675
        self.mov2.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov2)

        self.assertEqual(self.cuenta2.saldo_set.count(), cant_movs+1)
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2).importe,
            0 + 675
        )


class TestModelMovimientoSaveModificaEsGratis(TestModelMovimientoSave):

    def setUp(self):
        super().setUp()
        self.mov4 = Movimiento.crear(
            'traspaso entre titulares', 120, self.cuenta3, self.cuenta1)

    def test_mov_esgratis_false_elimina_contramovimiento(self):
        id_contramov = self.mov4.id_contramov
        self.mov4.esgratis = True
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(Movimiento.filtro(id=id_contramov).count(), 0)


class TestModelMovimientoConCuentaAcumulativaModificar(TestModelMovimientoSave):

    def setUp(self):
        super().setUp()
        self.mov4 = Movimiento.crear(
            'traspaso salida acum', 200, self.cuenta2, self.cuenta1)

        self.cuenta1 = dividir_en_dos_subcuentas(self.cuenta1)
        for mov in (self.mov1, self.mov2, self.mov3, self.mov4):
            mov.refresh_from_db()

    def test_no_puede_modificarse_importe_de_movimiento_con_cta_entrada_acumulativa(self):
        self.mov1.importe = 300
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov1.full_clean()

    def test_no_puede_modificarse_importe_de_movimiento_con_cta_salida_acumulativa(self):
        self.mov2.importe = 300
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov2.full_clean()

    def test_no_puede_modificarse_importe_de_mov_de_traspaso_con_una_cuenta_acumulativa(self):
        self.mov3.importe = 500
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov3.full_clean()

        self.mov4.importe = 500
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov4.full_clean()

    def test_no_puede_modificarse_importe_de_mov_de_traspaso_con_ambas_cuentas_acumulativa(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )

        self.mov3.importe = 600
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov3.full_clean()

    def test_no_puede_retirarse_cta_entrada_de_movimiento_si_es_acumulativa(self):
        self.mov1.cta_entrada = self.cuenta2
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov1.full_clean()

    def test_no_puede_retirarse_cta_salida_de_movimiento_si_es_acumulativa(self):
        self.mov2.cta_salida = self.cuenta2
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov2.full_clean()

    def test_no_puede_retirarse_cuenta_de_traspaso_si_es_acumulativa(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3')

        self.mov3.cta_entrada = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov3.full_clean()

        self.mov4.cta_salida = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov4.full_clean()

    def test_no_puede_retirarse_cuenta_de_traspaso_si_ambas_son_acumulativas(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3')
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )

        self.mov3.cta_entrada = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov3.full_clean()

        self.mov4.cta_salida = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov4.full_clean()

    def test_no_puede_agregarse_cta_entrada_acumulativa_a_movimiento(self):
        mov1 = Movimiento.crear('entrada', 100, self.cuenta2)
        mov2 = Movimiento.crear('salida', 100, None, self.cuenta2)

        mov1.cta_entrada = self.cuenta1
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_AGREGADA):
            mov1.full_clean()

        mov2.cta_entrada = self.cuenta1
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_AGREGADA):
            mov2.full_clean()

    def test_puede_agregarse_contracuenta_interactiva_a_entrada_con_cta_acumulativa(self):
        self.mov1.cta_salida = self.cuenta2
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.cta_salida, self.cuenta2)

    def test_puede_agregarse_contracuenta_interactiva_a_salida_con_cta_acumulativa(self):
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(self.mov2.cta_entrada, self.cuenta2)

    def test_puede_modificarse_cta_interactiva_en_movimiento_con_cta_entrada_acumulativa(self):
        self.mov3.cta_salida = self.cuenta2
        self.mov3.full_clean()
        self.mov3.save()
        self.assertEqual(self.mov3.cta_salida, self.cuenta2)

    def test_puede_modificarse_cta_interactiva_en_movimiento_con_cta_salida_acumulativa(self):
        self.mov4.cta_entrada = self.cuenta2
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(self.mov4.cta_entrada, self.cuenta2)

    def test_puede_retirarse_cta_interactiva_en_movimiento_con_cta_entrada_acumulativa(self):
        self.mov3.cta_salida = None
        self.mov3.full_clean()
        self.mov3.save()
        self.assertIsNone(self.mov3.cta_salida)

    def test_puede_retirarse_cta_interactiva_en_movimiento_con_cta_salida_acumulativa(self):
        self.mov4.cta_entrada = None
        self.mov4.full_clean()
        self.mov4.save()
        self.assertIsNone(self.mov4.cta_entrada)

    def test_no_puede_agregarse_cta_salida_acumulativa_a_movimiento(self):
        mov1 = Movimiento.crear('entrada', 100, self.cuenta2)
        mov2 = Movimiento.crear('salida', 100, None, self.cuenta2)

        mov1.cta_salida = self.cuenta1
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_AGREGADA):
            mov1.full_clean()

        mov2.cta_salida = self.cuenta1
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_AGREGADA):
            mov2.full_clean()

    def test_no_puede_eliminarse_movimiento_con_cuenta_acumulativa(self):
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.MOVIMIENTO_CON_CA_ELIMINADO
        ):
            self.mov1.delete()

    def test_puede_modificarse_concepto_en_movimiento_de_entrada_con_cuenta_acumulativa(self):
        self.mov1.concepto = 'entrada cambiada'
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.concepto, 'entrada cambiada')

    def test_puede_modificarse_concepto_en_movimiento_de_salida_con_cuenta_acumulativa(self):
        self.mov2.concepto = 'salida cambiada'
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(
            self.mov2.concepto, 'salida cambiada')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_entrada(self):
        self.mov3.concepto = 'entrada cambiada en traspaso'
        self.mov3.full_clean()
        self.mov3.save()
        self.assertEqual(
            self.mov3.concepto, 'entrada cambiada en traspaso')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_salida(self):
        self.mov4.concepto = 'salida cambiada en traspaso'
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(
            self.mov4.concepto, 'salida cambiada en traspaso')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_ambas_cuentas_acumulativas(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )
        self.mov4.concepto = 'concepto cambiado en traspaso'
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(
            self.mov4.concepto, 'concepto cambiado en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_entrada_con_cuenta_acumulativa(self):
        self.mov1.detalle = 'entrada cambiada'
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.detalle, 'entrada cambiada')

    def test_puede_modificarse_detalle_en_movimiento_de_salida_con_cuenta_acumulativa(self):
        self.mov2.detalle = 'salida cambiada'
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(
            self.mov2.detalle, 'salida cambiada')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_entrada(self):
        self.mov3.detalle = 'entrada cambiada en traspaso'
        self.mov3.full_clean()
        self.mov3.save()
        self.assertEqual(
            self.mov3.detalle, 'entrada cambiada en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_salida(self):
        self.mov4.detalle = 'salida cambiada en traspaso'
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(
            self.mov4.detalle, 'salida cambiada en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_ambas_cuentas_acumulativas(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )
        self.mov4.detalle = 'detalle cambiado en traspaso'
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(
            self.mov4.detalle, 'detalle cambiado en traspaso')

    def test_puede_modificarse_fecha_en_movimiento_con_cta_entrada_acumulativa_si_nueva_fecha_es_anterior_a_conversion(
            self):
        self.mov1.fecha = date(2020, 1, 5)
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.fecha, date(2020, 1, 5))

    def test_puede_modificarse_fecha_en_movimiento_con_cta_salida_acumulativa_si_nueva_fecha_es_anterior_a_conversion(
            self):
        self.mov2.fecha = date(2020, 1, 5)
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(self.mov2.fecha, date(2020, 1, 5))

    def test_no_puede_asignarse_fecha_posterior_a_conversion_en_mov_con_cta_entrada_acumulativa(self):
        self.mov1.fecha = date.today() + timedelta(days=2)
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                f'{errors.FECHA_POSTERIOR_A_CONVERSION}{date.today()}'
        ):
            self.mov1.full_clean()

    def test_no_puede_asignarse_fecha_posterior_a_conversion_en_mov_con_cta_salida_acumulativa(self):
        self.mov2.fecha = date.today() + timedelta(days=2)
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                f'{errors.FECHA_POSTERIOR_A_CONVERSION}{date.today()}'
        ):
            self.mov2.full_clean()
