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

    def test_resta_importe_antiguo_y_suma_el_nuevo_a_saldo_de_cta_entrada_en_movimiento(self):
        self.mov1.importe = 128
        self.mov1.save()
        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov1), 125-125+128)

    def test_suma_importe_antiguo_y_resta_el_nuevo_de_cta_salida_en_movimiento(self):
        self.mov2.importe = 37
        self.mov2.save()

        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov2), 90+35-37)

    def test_en_mov_de_traspaso_resta_importe_antiguo_y_suma_nuevo_en_saldo_cta_entrada_y_suma_importe_antiguo_y_resta_nuevo_en_saldo_cta_salida(self):
        saldo_ce = Saldo.tomar(cuenta=self.cuenta1, movimiento=self.mov3)
        saldo_cs = Saldo.tomar(cuenta=self.cuenta2, movimiento=self.mov3)

        self.mov3.importe = 60
        self.mov3.save()
        saldo_ce.refresh_from_db(fields=['_importe'])
        saldo_cs.refresh_from_db(fields=['_importe'])

        self.assertEqual(saldo_ce.importe, 140-50+60)
        self.assertEqual(saldo_cs.importe, -50+50-60)

    def test_actualiza_saldos_posteriores_de_cta_entrada(self):
        self.mov1.importe = 110
        self.mov1.save()

        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov2), 75)

    def test_actualiza_saldos_posteriores_de_cta_salida(self):
        self.mov2.importe = 37
        self.mov2.save()

        self.assertEqual(self.cuenta1.saldo_en_mov(self.mov3), 138)

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

    @patch('diario.models.movimiento.Saldo.generar')
    def test_cambiar_cta_entrada_genera_saldo_cta_entrada_nueva_en_movimiento(self, mock_generar):
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        mock_generar.assert_called_once_with(self.mov1, salida=False)

    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_cambiar_cta_entrada_elimina_saldo_de_cta_entrada_vieja_en_movimiento(self, mock_eliminar):
        saldo_ce = self.mov1.saldo_ce()
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        mock_eliminar.assert_called_once_with(saldo_ce)

    def test_cambiar_cta_entrada_actualiza_importe_de_saldos_posteriores_de_cta_anterior_y_nueva(self):
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90-125
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50+125
        )

    @patch('diario.models.movimiento.Saldo.generar')
    def test_cambiar_cta_salida_genera_saldo_cta_salida_nueva_en_movimiento(self, mock_generar):
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()
        mock_generar.assert_called_once_with(self.mov2, salida=True)

    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_cambiar_cta_salida_elimina_saldo_de_cta_salida_vieja_en_movimiento(self, mock_eliminar):
        saldo_cs = self.mov2.saldo_cs()
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()
        mock_eliminar.assert_called_once_with(saldo_cs)

    def test_cambiar_cta_salida_actualiza_importe_de_saldos_posteriores_de_cta_anterior_y_nueva(self):
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140+35
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50-35
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

    def test_modificar_ambas_cuentas_en_movimientos_de_traspaso_actualiza_importes_de_saldos_posteriores_de_las_cuatro_cuentas(self):
        cuenta3 = Cuenta.crear('cuenta 3', 'c3', fecha_creacion=date(2021, 1, 1))
        cuenta4 = Cuenta.crear('cuenta 4', 'c4', fecha_creacion=date(2021, 1, 1))

        mov4 = Movimiento.crear(
            'mov4', 1000, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 12))
        mov5 = Movimiento.crear(
            'mov5', 100, cuenta3, cuenta4, fecha=date(2021, 1, 15))

        self.mov3.cta_entrada = cuenta3
        self.mov3.cta_salida = cuenta4
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            1140-50
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=mov4).importe,
            -1050+50
        )
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=mov5).importe,
            100+50
        )
        self.assertEqual(
            cuenta4.saldo_set.get(movimiento=mov5).importe,
            -100-50
        )

    def test_intercambiar_cuentas_resta_importe_x2_de_saldo_en_movimiento_de_cta_entrada_y_lo_suma_a_saldo_en_movimiento_de_cta_salida(
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

    def test_intercambiar_cuentas_actualiza_importes_de_saldos_posteriores_de_cuentas_intercambiadas(self):
        mov4 = Movimiento.crear(
            'mov4', 1000, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 12))
        self.mov3.cta_salida = self.cuenta1
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            1140 - 50 * 2
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=mov4).importe,
            -1050 + 50 * 2
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

    def test_cambiar_cta_de_salida_a_entrada_actualiza_importes_de_saldos_posteriores_de_cuenta(self):
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 + 35 * 2
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

    def test_cambiar_cta_de_entrada_a_salida_actualiza_importes_de_saldos_posteriores_de_cuenta(self):
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90 - 125 * 2
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 125 * 2
        )

    def test_cuenta_de_salida_pasa_a_ser_de_entrada_y_cuenta_nueva_de_salida_en_traspaso(self):
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

    def test_si_cta_salida_pasa_a_entrada_y_aparece_cta_salida_nueva_en_traspaso_se_actualiza_importe_de_saldos_posteriores_de_las_tres_cuentas(self):
        cuenta3 = Cuenta.crear('cta3', 'c3', fecha_creacion=date(2021, 1, 1))
        mov4 = Movimiento.crear(
            'mov4', 1000, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 12))
        mov5 = Movimiento.crear(
            'mov5', 100, cuenta3, fecha=date(2021, 1, 15))

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            1140-50
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=mov4).importe,
            -1050 + 50 * 2
        )
        self.assertEqual(
            cuenta3.saldo_set.get(movimiento=mov5).importe,
            100 - 50
        )

    def test_cuenta_de_entrada_pasa_a_ser_de_salida_y_cuenta_nueva_de_entrada_en_traspaso(self):
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

    def test_si_cta_entrada_pasa_a_salida_y_aparece_cta_entrada_nueva_en_traspaso_se_actualiza_importe_de_saldos_posteriores_de_las_tres_cuentas(self):
        cuenta4 = Cuenta.crear('cta4', 'c4', fecha_creacion=date(2021, 1, 1))
        mov4 = Movimiento.crear(
            'mov4', 1000, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 12))
        mov5 = Movimiento.crear(
            'mov5', 100, None, cuenta4, fecha=date(2021, 1, 15))

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta4
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            1140 - 50 * 2
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=mov4).importe,
            -1050 + 50
        )
        self.assertEqual(
            cuenta4.saldo_set.get(movimiento=mov5).importe,
            -100 + 50
        )

    def test_cuenta_de_salida_desaparece(self):
        """ Suma importe a saldo de cta_salida retirada al momento del
            movimiento"""
        self.mov3.cta_salida = None
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta2, movimiento=self.mov3)

    def test_si_desaparece_cta_salida_en_traspaso_actualiza_importes_de_saldos_posteriores_de_cuenta(self):
        mov4 = Movimiento.crear(
            'mov4', 1000, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 12))
        self.mov3.cta_salida = None
        self.mov3.save()

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=mov4).importe,
            -1050 + 50
        )

    def test_cuenta_de_entrada_desaparece(self):
        """ Desaparece saldo de cuenta de entrada en movimiento"""
        self.mov3.cta_entrada = None
        self.mov3.save()

        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3)

    def test_si_desaparece_cta_entrada_en_traspaso_actualiza_importes_de_saldos_posteriores_de_cuenta(self):
        mov4 = Movimiento.crear(
            'mov4', 1000, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 12))
        self.mov3.cta_entrada = None
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            1140 - 50
        )

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

    def test_si_desaparece_cta_salida_y_cta_entrada_pasa_a_salida_actaualiza_importes_de_saldos_posteriores_de_ambas_cuentas(self):
        mov4 = Movimiento.crear(
            'mov4', 1000, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 12))
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            1140 - 50 * 2
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=mov4).importe,
            -1050 + 50
        )

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

    def test_si_desaparece_cta_entrada_y_cta_salida_pasa_a_entrada_actaualiza_importes_de_saldos_posteriores_de_ambas_cuentas(self):
        mov4 = Movimiento.crear(
            'mov4', 1000, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 12))
        self.mov3.cta_entrada = self.mov3.cta_salida  # self.cuenta2
        self.mov3.cta_salida = None
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            1140 - 50
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=mov4).importe,
            -1050 + 50 * 2
        )

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

    def test_si_aparece_cta_salida_actualiza_importe_de_saldos_posteriores_de_cuenta(self):
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 - 125
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

    def test_si_aparece_cta_entrada_actualiza_importe_de_saldos_posteriores_de_cuenta(self):
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.save()

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 35
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

    def test_si_cta_entrada_pasa_a_salida_y_aparece_nueva_cta_entrada_actualiza_importe_de_saldos_posteriores_de_ambas_cuentas(self):
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 125 * 2
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 125
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

    def test_si_cta_salida_pasa_a_entrada_y_aparece_nueva_cta_salida_actualiza_importe_de_saldos_posteriores_de_ambas_cuentas(self):
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 + 35 * 2
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 - 35
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

    def test_si_desaparece_cta_entrada_y_aparece_cta_salida_actualiza_importes_de_saldos_posteriores_de_ambas_cuentas(self):
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 - 125
        )

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 - 125
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

    def test_si_desaparece_cta_salida_y_aparece_cta_entrada_actualiza_importes_de_saldos_posteriores_de_ambas_cuentas(self):
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.cta_salida = None
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140 + 35
        )

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50 + 35
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


class TestModelMovimientoSaveModificaFecha(TestModelMovimientoSave):

    def test_si_cambia_fecha_a_fecha_posterior_toma_primer_orden_dia_de_nueva_fecha(self):
        mov4 = Movimiento.crear('mov4', 100, self.cuenta1, fecha=self.mov1.fecha)
        self.assertEqual(mov4.orden_dia, 1)

        mov4.fecha = self.mov3.fecha
        mov4.full_clean()
        mov4.save()

        self.assertEqual(mov4.orden_dia, 0)

    def test_si_cambia_fecha_a_fecha_anterior_toma_ultimo_orden_dia_de_nueva_fecha(self):
        Movimiento.crear('mov4', 100, self.cuenta1, fecha=self.mov1.fecha)

        self.mov2.fecha = self.mov1.fecha
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(self.mov2.orden_dia, 2)

    def test_si_cambia_fecha_a_fecha_posterior_resta_importe_a_saldos_intermedios_de_cta_entrada_entre_antigua_y_nueva_posicion_de_movimiento(self):
        self.mov1.fecha = date(2021, 1, 12)
        self.mov1.full_clean()
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90-125
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140-125
        )

    def test_si_cambia_fecha_a_fecha_posterior_suma_importe_a_saldos_intermedios_de_cta_salida_entre_antigua_y_nueva_posicion_de_movimiento(self):
        self.mov2.fecha = date(2021, 1, 12)
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140+35
        )

    def test_si_cambia_fecha_a_una_fecha_posterior_suma_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_entrada(self):
        self.mov1.fecha = date(2021, 1, 12)
        self.mov1.full_clean()
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            140-125+125
        )

    def test_si_cambia_fecha_a_una_fecha_posterior_resta_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_salida(self):
        self.mov2.fecha = date(2021, 1, 12)
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            125+50-35
        )

    def test_si_cambia_fecha_a_una_fecha_posterior_pero_anterior_a_todos_los_saldos_posteriores_de_cta_entrada_no_modifica_importe_de_ningun_saldo(self):

        self.mov1.fecha = date(2021, 1, 9)
        self.mov1.full_clean()
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            140
        )

    def test_si_cambia_fecha_a_una_fecha_posterior_pero_anterior_a_todos_los_saldos_posteriores_de_cta_salida_no_modifica_importe_de_ningun_saldo(self):
        mov4 = Movimiento.crear(
            'mov posterior', 90, self.cuenta2, fecha=date(2021, 1, 31))
        self.mov3.fecha = date(2021, 1, 12)
        self.mov3.full_clean()
        self.mov3.save()

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50
        )
        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=mov4).importe,
            40
        )

    def test_si_cambia_fecha_a_una_fecha_posterior_no_modifica_importes_de_saldos_de_cta_entrada_posteriores_a_nueva_ubicacion_de_movimiento(self):
        mov4 = Movimiento.crear(
            'mov posterior', 100, self.cuenta1, fecha=date(2021, 1, 31))
        self.mov1.fecha = date(2021, 1, 10)
        self.mov1.full_clean()
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            240
        )

    def test_si_cambia_fecha_a_una_fecha_posterior_no_modifica_importes_de_saldos_de_cta_salida_posteriores_a_nueva_ubicacion(self):
        mov4 = Movimiento.crear(
            'mov posterior', 100, self.cuenta1, fecha=date(2021, 1, 31))
        self.mov2.fecha = date(2021, 1, 12)
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            240
        )

    def test_si_cambia_fecha_a_una_fecha_posterior_no_modifica_importes_de_saldos_de_cta_entrada_anteriores_a_ubicacion_anterior_de_movimiento(self):
        mov4 = Movimiento.crear(
            'mov anterior', 100, self.cuenta1, fecha=date(2021, 1, 1))
        self.mov1.fecha = date(2021, 1, 10)
        self.mov1.full_clean()
        self.mov1.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            100
        )

    def test_si_cambia_fecha_a_una_fecha_posterior_no_modifica_importes_de_saldos_de_cta_salida_anteriores_a_ubicacion_anterior_de_movimiento(self):
        self.mov2.fecha = date(2021, 1, 12)
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125
        )

    def test_si_cambia_fecha_a_fecha_anterior_suma_importe_a_saldos_intermedios_de_cta_entrada_entre_antigua_y_nueva_posicion_de_movimiento(self):
        self.mov3.fecha = date(2021, 1, 1)
        self.mov3.full_clean()
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125+50
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90+50
        )

    def test_si_cambia_fecha_a_fecha_anterior_resta_importe_a_saldos_intermedios_de_cta_salida_entre_antigua_y_nueva_posicion_de_movimiento(self):
        self.mov2.fecha = date(2021, 1, 1)
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(
            # Saldo.tomar(cuenta=self.cuenta2, movimiento=self.mov1).importe,
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125-35
        )

    def test_si_cambia_fecha_a_una_fecha_anterior_suma_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_entrada(self):
        self.mov3.fecha = date(2021, 1, 6)
        self.mov3.full_clean()
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            125+50
        )

    def test_si_cambia_fecha_a_una_fecha_anterior_resta_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_salida(self):
        mov4 = Movimiento.crear(
            'mov4', 100, None, self.cuenta1, fecha=date(2021, 1, 31))
        mov4.fecha = date(2021, 1, 6)
        mov4.full_clean()
        mov4.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            125-100
        )

    def test_si_cambia_fecha_a_una_fecha_anterior_y_no_hay_saldo_anterior_de_cta_entrada_asigna_importe_del_movimiento_a_saldo_de_cta_entrada_en_nueva_ubicacion_del_movimiento(self):
        self.mov3.fecha = date(2021, 1, 1)
        self.mov3.full_clean()
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov3).importe,
            50
        )

    def test_si_cambia_fecha_a_una_fecha_anterior_y_no_hay_saldo_anterior_de_cta_salida_asigna_importe_del_movimiento_en_negativo_a_saldo_de_cta_salida_en_nueva_ubicacion_del_movimiento(self):
        self.mov3.fecha = date(2021, 1, 1)
        self.mov3.full_clean()
        self.mov3.save()

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov3).importe,
            -50
        )

    def test_si_cambia_fecha_a_una_fecha_anterior_no_modifica_importes_de_saldos_de_cta_entrada_anteriores_a_nueva_ubicacion_de_movimiento(self):
        self.mov3.fecha = date(2021, 1, 6)
        self.mov3.full_clean()
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125
        )

    def test_si_cambia_fecha_a_una_fecha_anterior_no_modifica_importes_de_saldos_de_cta_salida_anteriores_a_nueva_ubicacion(self):
        mov4 = Movimiento.crear(
            'mov posterior', 100, None, self.cuenta1, fecha=date(2021, 1, 31))
        mov4.fecha = date(2021, 1, 6)
        mov4.full_clean()
        mov4.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov1).importe,
            125
        )

    def test_si_cambia_fecha_a_una_fecha_anterior_no_modifica_importes_de_saldos_de_cta_entrada_posteriores_a_ubicacion_anterior_de_movimiento(self):
        mov4 = Movimiento.crear(
            'mov anterior', 100, self.cuenta1, fecha=date(2021, 1, 31))
        self.mov3.fecha = date(2021, 1, 10)
        self.mov3.full_clean()
        self.mov3.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            240
        )

    def test_si_cambia_fecha_a_una_fecha_anterior_no_modifica_importes_de_saldos_de_cta_salida_posteriores_a_ubicacion_anterior_de_movimiento(self):
        mov4 = Movimiento.crear(
            'mov anterior', 100, self.cuenta1, fecha=date(2021, 1, 31))
        self.mov2.fecha = date(2021, 1, 12)
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=mov4).importe,
            240
        )


class TestModelMovimientoSaveModificaOrdenDia(TestModelMovimientoSave):

    def setUp(self):
        super().setUp()
        self.mov2a = Movimiento.crear(
            'mov2a', 100, self.cuenta1, fecha=self.mov2.fecha)
        self.mov2b = Movimiento.crear(
            'mov2b', 20, self.cuenta2, self.cuenta1, fecha=self.mov2.fecha)
        self.mov2c = Movimiento.crear(
            'mov2c', 30, self.cuenta1, self.cuenta2, fecha=self.mov2.fecha)

    def test_si_cambia_orden_dia_a_un_orden_posterior_resta_importe_de_saldos_intermedios_de_cta_entrada(self):
        self.mov2a.orden_dia = 3
        self.mov2a.full_clean()
        self.mov2a.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2b).importe,
            170-100
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2c).importe,
            200-100
        )

    def test_si_cambia_orden_dia_a_un_orden_posterior_suma_importe_a_saldos_intermedios_de_cta_salida(self):
        self.mov2.orden_dia = 3
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2a).importe,
            190+35
        )

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2b).importe,
            170+35
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2c).importe,
            200+35
        )

    def test_si_cambia_orden_dia_a_un_orden_posterior_suma_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_entrada(self):
        self.mov2a.orden_dia = 3
        self.mov2a.full_clean()
        self.mov2a.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2a).importe,
            100+100
        )

    def test_si_cambia_orden_dia_a_un_orden_posterior_resta_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_salida(self):
        self.mov2.orden_dia = 3
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            235-35
        )

    def test_si_cambia_orden_dia_a_un_orden_posterior_no_modifica_importe_de_saldos_de_cta_entrada_posteriores_a_nueva_ubicacion_de_movimiento(self):
        self.mov2a.orden_dia = 2
        self.mov2a.full_clean()
        self.mov2a.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2c).importe,
            200
        )

    def test_si_cambia_orden_dia_a_un_orden_posterior_no_modifica_importe_de_saldos_de_cta_salida_posteriores_a_nueva_ubicacion_de_movimiento(self):
        self.mov2.orden_dia = 2
        self.mov2.full_clean()
        self.mov2.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2c).importe,
            200
        )

    def test_si_cambia_orden_dia_a_un_orden_posterior_no_modifica_importes_de_saldos_de_cta_entrada_anteriores_a_ubicacion_anterior_de_movimiento(self):
        self.mov2a.orden_dia = 2
        self.mov2a.full_clean()
        self.mov2a.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90
        )

    def test_si_cambia_orden_dia_a_un_orden_posterior_no_modifica_importes_de_saldos_de_cta_salida_anteriores_a_ubicacion_anterior_de_movimiento(self):
        self.mov2b.orden_dia = 3
        self.mov2b.full_clean()
        self.mov2b.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2a).importe,
            190
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_suma_importe_a_saldos_intermedios_de_cta_entrada(self):
        self.mov2c.orden_dia = 1
        self.mov2c.full_clean()
        self.mov2c.save()
        self.mov2a.refresh_from_db()
        self.mov2b.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2a).importe,
            190+30
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2b).importe,
            170+30
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_resta_importe_a_saldos_intermedios_de_cta_salida(self):
        self.mov2b.orden_dia = 0
        self.mov2b.full_clean()
        self.mov2b.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90-20
        )
        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2a).importe,
            190-20
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_suma_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_entrada(self):
        self.mov2c.orden_dia = 1
        self.mov2c.full_clean()
        self.mov2c.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2c).importe,
            90+30
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_resta_importe_del_movimiento_a_importe_del_nuevo_ultimo_saldo_anterior_de_cta_salida(self):
        self.mov2b.orden_dia = 0
        self.mov2b.full_clean()
        self.mov2b.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2b).importe,
            125-20
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_y_no_hay_saldo_anterior_de_cta_entrada_asigna_importe_del_movimiento_a_saldo_cta_entrada_en_nueva_ubicacion_del_movimiento(self):
        # se evalúa cuenta2
        self.mov2b.orden_dia = 0
        self.mov2b.full_clean()
        self.mov2b.save()

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2b).importe,
            self.mov2b.importe  # 20
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_y_no_hay_saldo_anterior_de_cta_salida_asigna_importe_del_movimiento_a_en_negativo_de_saldo_cta_salida_en_nueva_ubicacion_del_movimiento(self):
        # se evalúa cuenta2
        self.mov2c.orden_dia = 0
        self.mov2c.full_clean()
        self.mov2c.save()

        self.assertEqual(
            self.cuenta2.saldo_set.get(movimiento=self.mov2c).importe,
            -self.mov2c.importe  # -20
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_no_modifica_importes_de_saldos_de_cta_entrada_anteriores_a_nueva_ubicacion_de_movimiento(self):
        self.mov2c.orden_dia = 1
        self.mov2c.full_clean()
        self.mov2c.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_no_modifica_importes_de_saldos_de_cta_entrada_posteriores_a_ubicacion_anterior_de_movimiento(self):
        self.mov2a.orden_dia = 0
        self.mov2a.full_clean()
        self.mov2a.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2b).importe,
            170
        )

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2c).importe,
            200
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_no_modifica_importes_de_saldos_de_cta_salida_anteriores_a_nueva_ubicacion_de_movimiento(self):
        self.mov2b.orden_dia = 1
        self.mov2b.full_clean()
        self.mov2b.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2).importe,
            90
        )

    def test_si_cambia_orden_dia_a_un_orden_anterior_no_modifica_importes_de_saldos_de_cta_salida_posteriores_a_ubicacion_anterior_de_movimiento(self):
        self.mov2b.orden_dia = 1
        self.mov2b.full_clean()
        self.mov2b.save()

        self.assertEqual(
            self.cuenta1.saldo_set.get(movimiento=self.mov2c).importe,
            200
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
