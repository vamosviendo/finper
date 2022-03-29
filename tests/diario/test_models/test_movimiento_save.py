from datetime import date, timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError

from diario.models import Cuenta, Movimiento, Titular
from utils import errors
from utils.helpers_tests import dividir_en_dos_subcuentas

from .test_movimiento import TestModelMovimientoSave


class TestModelMovimientoSaveGeneral(TestModelMovimientoSave):

    def test_no_modifica_saldo_de_cuentas_si_no_se_modifica_importe_ni_cuentas(self):
        self.mov3.concepto = 'Depósito en efectivo'
        self.mov3.save()

        self.cuenta1.refresh_from_db()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, 140)
        self.assertEqual(self.cuenta2.saldo, -50)

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

    @patch('diario.models.movimiento.Movimiento._mantiene_cuenta')
    def test_verifica_cambios_en_cuentas_de_entrada_y_salida(self, mock_mantiene_cuenta):
        self.mov3.save()
        mock_mantiene_cuenta.assert_called()
        self.assertEqual(len(mock_mantiene_cuenta.call_args_list), 2)
        self.assertIn(
            'cta_entrada',
            mock_mantiene_cuenta.call_args_list[0].args
        )
        self.assertIn(
            'cta_salida',
            mock_mantiene_cuenta.call_args_list[1].args
        )


class TestModelMovimientoSaveModificaImporte(TestModelMovimientoSave):

    def test_resta_importe_antiguo_y_suma_el_nuevo_a_cta_entrada(self):
        self.mov1.importe = 128
        self.mov1.save()
        self.cuenta1.refresh_from_db()
        self.assertEqual(
            self.cuenta1.saldo, 140-125+128)

    def test_suma_importe_antiguo_y_resta_el_nuevo_a_cta_salida(self):
        self.mov2.importe = 37
        self.mov2.save()
        self.cuenta1.refresh_from_db()
        self.assertEqual(
            self.cuenta1.saldo, 140+35-37)

    def test_en_mov_traspaso_actua_sobre_las_dos_cuentas(self):
        """ Resta importe antiguo y suma nuevo a cta_entrada
            Suma importe antiguo y resta nuevo a cta_salida"""
        self.mov3.importe = 60
        self.mov3.save()
        self.refresh_ctas()
        self.assertEqual(
            self.cuenta1.saldo, 140-50+60)
        self.assertEqual(
            self.cuenta2.saldo, -50+50-60)

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

        cta_deudora.refresh_from_db(fields=['_saldo'])
        cta_acreedora.refresh_from_db(fields=['_saldo'])
        self.assertEqual(cta_deudora.saldo, -45)
        self.assertEqual(cta_acreedora.saldo, 45)


class TestModelMovimientoSaveModificaCuentas(TestModelMovimientoSave):

    def test_modificar_cta_entrada_resta_importe_de_saldo_cuenta_anterior_y_lo_suma_a_cuenta_nueva(self):
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-125)
        self.assertEqual(self.cuenta2.saldo, -50+125)

    def test_modificar_cta_salida_suma_importe_a_saldo_cuenta_anterior_y_lo_resta_de_cuenta_nueva(self):
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()
        self.refresh_ctas()
        self.assertEqual(self.cuenta2.saldo, -50-35)
        self.assertEqual(self.cuenta1.saldo, 140+35)

    def test_modificar_cta_entrada_funciona_en_movimientos_de_traspaso(self):
        """ Resta importe de cta_entrada vieja y lo suma a la nueva."""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)
        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(cuenta3.saldo, 0+50)

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

    def test_cambiar_cta_entrada_por_cta_otro_titular_en_movimiento_de_traspaso_con_contramovimiento_modifica_contramovimiento(self):
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

    def test_cambiar_cta_salida_por_cta_otro_titular_en_movimiento_de_traspaso_con_contramovimiento_modifica_contramovimiento(self):
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

    def test_cambiar_cta_salida_por_cta_mismo_titular_de_cta_entrada_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento(self):
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

    def test_modificar_cta_salida_funciona_en_movimientos_de_traspaso(self):
        """ Suma importe a cta_salida vieja y lo suma a la nueva"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        self.mov3.cta_salida = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)
        self.assertEqual(self.cuenta2.saldo, -50+50)
        self.assertEqual(cuenta3.saldo, 0-50)

    def test_modificar_ambas_cuentas_funciona_en_movimientos_de_traspaso(self):
        """ Resta importe a cta_entrada vieja y lo suma a la nueva
            Suma importe a cta_salida vieja y lo suma a la nueva"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        cuenta4 = Cuenta.crear('Colchón', 'c')
        saldo3 = cuenta3.saldo
        saldo4 = cuenta4.saldo

        self.mov3.cta_entrada = cuenta3
        self.mov3.cta_salida = cuenta4
        self.mov3.save()
        self.refresh_ctas(cuenta3, cuenta4)

        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(cuenta3.saldo, 0+50)
        self.assertEqual(self.cuenta2.saldo, -50+50)
        self.assertEqual(cuenta4.saldo, 0-50)

    def test_intercambiar_cuentas_resta_importe_x2_de_cta_entrada_y_lo_suma_a_cta_salida(self):
        """ Resta dos veces importe de vieja cta_entrada (ahora cta_salida)
            Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov3.cta_salida = self.cuenta1
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, -50 + 50*2)
        self.assertEqual(self.cuenta1.saldo, 140 - 50*2)

    def test_cuenta_de_salida_pasa_a_ser_de_entrada(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, 140 + 35*2)

    def test_cuenta_de_entrada_pasa_a_ser_de_salida(self):
        """ Resta dos veces importe a vieja cta_entrada (ahora cta_salida)"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, 140 - 125*2)

    def test_cuenta_de_salida_pasa_a_ser_de_entrada_y_cuenta_nueva_de_salida(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)
            Resta importe de nueva cta_salida"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(self.cuenta2.saldo, -50+50*2)
        self.assertEqual(cuenta3.saldo, 0-50)

    def test_cuenta_de_entrada_pasa_a_ser_de_salida_y_cuenta_nueva_de_entrada(self):
        """ Resta dos veces importe a vieja cta_entrada (ahora cta_salida
            Suma importe a nueva cta_entrada """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, 140-50*2)
        self.assertEqual(self.cuenta2.saldo, -50+50)
        self.assertEqual(cuenta3.saldo, 0+50)

    def test_cuenta_de_salida_desaparece(self):
        """ Suma importe a cta_salida retirada"""
        self.mov3.cta_salida = None
        self.mov3.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, -50+50)

    def test_cuenta_de_entrada_desaparece(self):
        """ Resta importe a cta_entrada retirada"""
        self.mov3.cta_entrada = None
        self.mov3.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, 140-50)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida(self):
        """ Suma importe a cta_salida retirada
            Resta dos veces a vieja cta_entrada (ahora cta_salida) """
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-50*2)
        self.assertEqual(self.cuenta2.saldo, -50+50)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada(self):
        """ Resta importe a cta_entrada retirada
            Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(self.cuenta2.saldo, -50+50*2)

    def test_aparece_cuenta_de_salida(self):
        """ Resta importe de nueva cta_salida """
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, -50-125)

    def test_aparece_cuenta_de_entrada(self):
        """ Suma importe a nueva cta_entrada """
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, 140+35)

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada(self):
        """ Resta dos veces importe de vieja cta_entrada (ahora cta_salida)
            Suma importe a nueva cta_entrada"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-125*2)
        self.assertEqual(self.cuenta2.saldo, -50+125)

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)
            Resta importe de nueva cta_salida """
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, -50-35)
        self.assertEqual(self.cuenta1.saldo, 140+35*2)

    def test_desaparece_cta_entrada_y_aparece_cta_de_salida(self):
        """ Resta importe de cta_entrada retirada
            Resta importe de cta_salida agregada """
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-125)
        self.assertEqual(self.cuenta2.saldo, -50-125)

    def test_desaparece_cta_salida_y_aparece_cta_de_entrada(self):
        """ Suma importe a cta_salida retirada
            Suma importe a cta_entrada agregada"""
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.cta_salida = None
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, -50+35)
        self.assertEqual(self.cuenta1.saldo, 140+35)


class TestModelMovimientoSaveModificaImporteYCuentas(TestModelMovimientoSave):

    def test_cambia_cuenta_de_entrada_con_nuevo_importe(self):
        """ Resta viejo importe de cta_entrada vieja
            Suma nuevo importe a cta_entrada nueva """
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 128
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-125)
        self.assertEqual(self.cuenta2.saldo, -50+128)

    def test_cambia_cuenta_de_salida_con_nuevo_importe(self):
        """ Suma viejo importe a cta_salida vieja
            Resta nuevo importe de cta_salida nueva """
        self.mov2.cta_salida = self.cuenta2
        self.mov2.importe = 63
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, -50-self.mov2.importe)
        self.assertEqual(self.cuenta1.saldo, 140+35)

    def test_cambia_cuenta_de_entrada_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Resta importe viejo de cta_entrada vieja
            Suma importe nuevo a cta_entrada nueva
            Suma importe viejo y resta importe nuevo a cta_salida """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_entrada = cuenta3
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)
        self.assertEqual(
            self.cuenta2.saldo,
            -50+50-self.mov3.importe
        )

    def test_cambia_cuenta_de_salida_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida vieja
            Resta importe nuevo de cta_salida nueva
            Resta importe viejo y suma importe nuevo a cta_entrada """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta2.saldo, -50+50)
        self.assertEqual(cuenta3.saldo, 0-56)
        self.assertEqual(
            self.cuenta1.saldo,
            140-50+56
        )

    def test_cambian_ambas_cuentas_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Resta importe viejo de cta_entrada vieja
            Suma importe nuevo a cta_entrada nueva
            Suma importe viejo a cta_salida vieja
            Suma importe nuevo a cta_entrada nueva """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        cuenta4 = Cuenta.crear('Colchón', 'ch')

        self.mov3.cta_entrada = cuenta3
        self.mov3.cta_salida = cuenta4
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3, cuenta4)

        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(self.cuenta2.saldo, -50+50)
        self.assertEqual(cuenta3.saldo, 0+56)
        self.assertEqual(cuenta4.saldo, 0-56)

    def test_se_intercambian_cuentas_de_entrada_y_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo de cta_entrada vieja
                (ahora cta_salida)
            Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada) """
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.cta_salida = self.cuenta1
        self.mov3.importe = 456
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, 140-50-456)
        self.assertEqual(
            self.cuenta2.saldo, -50+50+456)

    def test_cta_entrada_pasa_a_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a cta_entrada vieja
                (ahora cta_salida)"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.importe = 128
        self.mov1.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, 140-125-128)

    def test_cta_salida_pasa_a_entrada_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada) """
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.importe = 128
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, 140+35+128)

    def test_cta_salida_pasa_entrada_y_cta_salida_nueva_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada)
            Resta importe viejo de cta_entrada vieja
            Suma importe nuevo a cta_entrada nueva """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 252
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(
            self.cuenta2.saldo, -50+50+252)
        self.assertEqual(cuenta3.saldo, 0-252)

    def test_cta_entrada_pasa_salida_y_cta_entrada_nueva_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a cta_entrada vieja
                (ahora cta_salida)
            Resta importe viejo de cta_salida vieja
            Suma importe nuevo a cta_entrada nueva"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta3
        self.mov3.importe = 165
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, 140-50-165)
        self.assertEqual(self.cuenta2.saldo, -50+50)
        self.assertEqual(cuenta3.saldo, 0+165)

    def test_cuenta_de_salida_desaparece_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida retirada
            Resta importe viejo y suma importe nuevo a cta_entrada"""
        self.mov3.cta_salida = None
        self.mov3.importe = 234
        self.mov3.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, 140-50+234)
        self.assertEqual(self.cuenta2.saldo, -50+50)

    def test_cuenta_de_entrada_desaparece_con_nuevo_importe(self):
        """ Resta importe viejo a cta_entrada retirada
            Suma importe viejo y resta importe nuevo a cta_salida"""
        self.mov3.cta_entrada = None
        self.mov3.importe = 234
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(self.cuenta2.saldo, -50+50-234)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a vieja cta_entrada
                (ahora cta_salida)
            Suma importe viejo a cta_salida retirada """
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.importe = 350
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-50-350)
        self.assertEqual(self.cuenta2.saldo, -50+50)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a vieja cta_salida
                (ahora cta_entrada)
            Resta importe viejo a cta_entrada retirada """
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.importe = 354
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-50)
        self.assertEqual(self.cuenta2.saldo, -50+50+354)

    def test_aparece_cuenta_de_salida_con_nuevo_importe(self):
        """ Resta importe viejo y suma importe nuevo a cta_entrada
            Resta importe nuevo a cta_salida nueva"""
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 255
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-125+255)
        self.assertEqual(self.cuenta2.saldo, -50-255)

    def test_aparece_cuenta_de_entrada_con_nuevo_importe(self):
        """ Suma importe viejo y resta importe nuevo a cta_salida
            Suma importe nuevo a cta_entrada nueva"""
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.importe = 446
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, -50+446)
        self.assertEqual(self.cuenta1.saldo, 140+35-446)

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo de antigua cta_entrada
                (ahora cta_salida)
            Suma importe nuevo a cta_entrada agregada"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 556
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-125-556)
        self.assertEqual(self.cuenta2.saldo, -50+556)

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo de antigua cta_salida
                (ahora cta_entrada)
            Resta importe nuevo de cta_salida nueva """
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta2
        self.mov2.importe = 445
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, -50-445)
        self.assertEqual(self.cuenta1.saldo, 140+35+445)

    def test_desaparece_cta_entrada_y_aparece_otra_cta_de_salida_con_nuevo_importe(self):
        """ Resta importe viejo de cta_entrada retirada
            Resta importe nuevo de cta_salida agregada """
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 565
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, 140-125)
        self.assertEqual(self.cuenta2.saldo, -50-565)

    def test_desaparece_cta_salida_y_aparece_otra_cta_de_entrada_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida retirada
            Suma importe nuevo a cta_entrada agregada """
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.cta_salida = None
        self.mov2.importe = 675
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, -50+675)
        self.assertEqual(self.cuenta1.saldo, 140+35)


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

    def test_puede_modificarse_fecha_en_movimiento_con_cta_entrada_acumulativa_si_nueva_fecha_es_anterior_a_conversion(self):
        self.mov1.fecha = date(2020, 1, 5)
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.fecha, date(2020, 1, 5))

    def test_puede_modificarse_fecha_en_movimiento_con_cta_salida_acumulativa_si_nueva_fecha_es_anterior_a_conversion(self):
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


