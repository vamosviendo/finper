from datetime import date, timedelta
from unittest import skip

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento
from utils import errors
from utils.helpers_tests import dividir_en_dos_subcuentas


class TestModelMovimiento(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta1 = Cuenta.crear(nombre='Efectivo', slug='e')


class TestModelMovimientoBasic(TestModelMovimiento):

    def test_guarda_y_recupera_movimientos(self):
        primer_mov = Movimiento()
        primer_mov.fecha = date.today()
        primer_mov.concepto = 'entrada de efectivo'
        primer_mov.importe = 985.5
        primer_mov.cta_entrada = self.cuenta1
        primer_mov.save()

        segundo_mov = Movimiento()
        segundo_mov.fecha = date(2021, 4, 28)
        segundo_mov.concepto = 'compra en efectivo'
        segundo_mov.detalle = 'salchichas, pan, mostaza'
        segundo_mov.importe = 500
        segundo_mov.cta_salida = self.cuenta1
        segundo_mov.save()

        movs_guardados = Movimiento.todes()
        self.assertEqual(movs_guardados.count(), 2)

        primer_mov_guardado = Movimiento.tomar(pk=primer_mov.pk)
        segundo_mov_guardado = Movimiento.tomar(pk=segundo_mov.pk)

        self.assertEqual(primer_mov_guardado.fecha, date.today())
        self.assertEqual(primer_mov_guardado.concepto, 'entrada de efectivo')
        self.assertEqual(primer_mov_guardado.importe, 985.5)
        self.assertEqual(primer_mov_guardado.cta_entrada, self.cuenta1)

        self.assertEqual(segundo_mov_guardado.fecha, date(2021, 4, 28))
        self.assertEqual(segundo_mov_guardado.concepto, 'compra en efectivo')
        self.assertEqual(
            segundo_mov_guardado.detalle, 'salchichas, pan, mostaza')
        self.assertEqual(segundo_mov_guardado.importe, 500)
        self.assertEqual(segundo_mov_guardado.cta_salida, self.cuenta1)

    def test_cta_entrada_se_relaciona_con_cuenta(self):
        mov = Movimiento(
            fecha=date.today(), concepto='Cobranza en efectivo', importe=100)
        mov.cta_entrada = self.cuenta1
        mov.save()
        self.assertIn(mov, self.cuenta1.entradas.all())

    def test_cta_salida_se_relaciona_con_cuenta(self):
        mov = Movimiento(
            fecha=date.today(), concepto='Cobranza en efectivo', importe=100)
        mov.cta_salida = self.cuenta1
        mov.save()
        self.assertIn(mov, self.cuenta1.salidas.all())

    def test_cta_entrada_es_interactiva(self):
        mov = Movimiento.crear(
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1
        )
        self.assertTrue(mov.cta_entrada.es_interactiva)

    def test_permite_guardar_cuentas_de_entrada_y_salida_en_un_movimiento(self):
        cuenta2 = Cuenta.crear(nombre='Banco', slug='B')
        mov = Movimiento(
            fecha=date.today(),
            concepto='Retiro de efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=cuenta2
        )

        mov.full_clean()    # No debe dar error
        mov.save()

        self.assertIn(mov, self.cuenta1.entradas.all())
        self.assertIn(mov, cuenta2.salidas.all())
        self.assertNotIn(mov, self.cuenta1.salidas.all())
        self.assertNotIn(mov, cuenta2.entradas.all())

    def test_requiere_al_menos_una_cuenta(self):
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100
        )
        with self.assertRaisesMessage(
                ValidationError, errors.CUENTA_INEXISTENTE
        ):
            mov.full_clean()

    def test_no_admite_misma_cuenta_de_entrada_y_de_salida(self):
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta1
        )
        with self.assertRaisesMessage(ValidationError, errors.CUENTAS_IGUALES):
            mov.full_clean()

    def test_movimiento_str(self):
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        mov1 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Retiro de efectivo',
            importe='250.2',
            cta_entrada=self.cuenta1,
            cta_salida=cta2
        )
        mov2 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Carga de saldo',
            importe='500',
            cta_entrada=self.cuenta1,
        )
        mov3 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Transferencia',
            importe='300.35',
            cta_salida=cta2
        )
        self.assertEqual(
            str(mov1),
            '2021-03-22 Retiro de efectivo: 250.2 +efectivo -banco'
        )
        self.assertEqual(
            str(mov2),
            '2021-03-22 Carga de saldo: 500 +efectivo'
        )
        self.assertEqual(
            str(mov3),
            '2021-03-22 Transferencia: 300.35 -banco'
        )

    def test_guarda_fecha_de_hoy_por_defecto(self):
        mov = Movimiento.crear(
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1
        )
        self.assertEqual(mov.fecha, date.today())

    def test_permite_movimientos_duplicados(self):
        Movimiento.crear(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1
        )
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1
        )
        mov.full_clean()    # No debe dar error

    def test_movimientos_se_ordenan_por_fecha(self):
        mov1 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Pago en efectivo',
            importe=100,
            cta_salida=self.cuenta1,
        )
        mov2 = Movimiento.crear(
            fecha=date(2021, 4, 2),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
        )
        mov3 = Movimiento.crear(
            fecha=date(2020, 10, 22),
            concepto='Cobranza en efectivo',
            importe=243,
            cta_entrada=self.cuenta1,
        )

        self.assertEqual(list(Movimiento.todes()), [mov3, mov2, mov1])

    def test_dentro_de_fecha_movimientos_se_ordenan_por_campo_orden_dia(self):
        mov1 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Mov1',
            importe=100,
            cta_salida=self.cuenta1,
        )
        mov2 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Mov2',
            importe=100,
            cta_entrada=self.cuenta1,
        )
        mov3 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Mov3',
            importe=243,
            cta_entrada=self.cuenta1,
        )

        mov3.orden_dia = 0
        mov3.full_clean()
        mov3.save()
        mov1.refresh_from_db()
        mov2.refresh_from_db()

        self.assertEqual(list(Movimiento.todes()), [mov3, mov1, mov2])



class TestModelMovimientoCrear(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear(nombre='Banco', slug='b')

    def test_crear_funciona_con_args_basicos_sin_nombre(self):
        mov1 = Movimiento.crear('Pago en efectivo', 100, None, self.cuenta1)
        mov2 = Movimiento.crear('Cobranza en efectivo', 100, self.cuenta1)
        mov3 = Movimiento.crear(
            'Extracción bancaria', 50, self.cuenta1, self.cuenta2)
        self.assertEqual(mov1.concepto, 'Pago en efectivo')
        self.assertIsNone(mov1.cta_entrada)
        self.assertEqual(mov2.cta_entrada, self.cuenta1)
        self.assertIsNone(mov2.cta_salida)
        self.assertEqual(mov3.cta_salida, self.cuenta2)

    def test_funciona_con_argumentos_mixtos(self):
        mov1 = Movimiento.crear(
            'Pago en efectivo', 100, None, self.cuenta1,
            fecha=date(2020, 10, 22),
        )
        mov2 = Movimiento.crear(
            'Cobranza en efectivo', 100, self.cuenta1, detalle='Alquiler')
        mov3 = Movimiento.crear(
            'Pago en efectivo', 100, cta_salida=self.cuenta1)

        self.assertEqual(mov1.fecha, date(2020, 10, 22))
        self.assertEqual(mov2.detalle, 'Alquiler')
        self.assertIsNone(mov2.cta_salida)
        self.assertEqual(mov3.cta_salida, self.cuenta1)
        self.assertIsNone(mov3.cta_entrada)

    def test_mov_entrada_con_importe_negativo_se_convierte_en_mov_salida(self):
        mov = Movimiento.crear('Pago', -100, cta_entrada=self.cuenta1)
        self.assertIsNone(mov.cta_entrada)
        self.assertEqual(mov.cta_salida, self.cuenta1)

    def test_mov_salida_con_importe_negativo_se_convierte_en_mov_entrada(self):
        mov = Movimiento.crear('Pago', -100, cta_salida=self.cuenta1)
        self.assertIsNone(mov.cta_salida)
        self.assertEqual(mov.cta_entrada, self.cuenta1)

    def test_mov_traspaso_con_importe_negativo_intercambia_cta_entrada_y_salida(self):
        mov = Movimiento.crear(
            'Pago', -100, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertEqual(mov.cta_salida, self.cuenta2)
        self.assertEqual(mov.cta_entrada, self.cuenta1)

    def test_mov_con_importe_negativo_se_guarda_con_importe_positivo(self):
        mov = Movimiento.crear('Pago', -100, cta_entrada=self.cuenta1)
        self.assertEqual(mov.importe, 100)

    def test_importe_cero_tira_error(self):
        with self.assertRaisesMessage(
                errors.ErrorImporteCero,
                "Se intentó crear un movimiento con importe cero"
        ):
            mov = Movimiento.crear('Pago', 0, cta_salida=self.cuenta1)

    def test_acepta_importe_en_formato_str(self):
        mov = Movimiento.crear('Pago', '200', cta_entrada=self.cuenta1)
        self.assertEqual(mov.importe, 200.0)


class TestModelMovimientoPropiedades(TestModelMovimiento):

    def test_sentido_devuelve_resultado_segun_cuentas_presentes(self):
        mov1 = Movimiento.crear(
            concepto='Pago en efectivo',
            importe=100,
            cta_salida=self.cuenta1,
        )
        mov2 = Movimiento.crear(
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
        )
        cuenta2 = Cuenta.crear("Banco", "bco")
        mov3 = Movimiento.crear(
            concepto='Pago a cuenta',
            importe=143,
            cta_entrada=cuenta2,
            cta_salida=self.cuenta1,
        )
        self.assertEqual(mov1.sentido, 's')
        self.assertEqual(mov2.sentido, 'e')
        self.assertEqual(mov3.sentido, 't')


class TestModelMovimientoPropiedadImporte(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.mov = Movimiento(concepto='Movimiento con importe', _importe=100, cta_entrada=self.cuenta1)
        self.mov.full_clean()
        self.mov.save()

    def test_devuelve_importe_del_movimiento(self):
        self.assertEqual(self.mov.importe, self.mov._importe)

    def test_asigna_valor_a_campo__importe(self):
        self.mov.importe = 300
        self.assertEqual(self.mov._importe, 300)

    def test_redondea_importe(self):
        self.mov.importe = 300.462
        self.assertEqual(self.mov._importe, 300.46)

    def test_funciona_con_strings(self):
        self.mov.importe = '200'
        self.assertEqual(self.mov._importe, 200)

    def test_redondea_strings(self):
        self.mov.importe = '222.2222'
        self.assertEqual(self.mov._importe, 222.22)


class TestModelMovimientoMetodos(TestModelMovimiento):

    def test_tiene_cuenta_acumulativa_devuelve_true_si_mov_tiene_una_cuenta_acumulativa(self):
        cuenta2 = Cuenta.crear('cuenta2', 'c2')
        mov = Movimiento.crear(
            'traspaso', 100, cta_entrada=self.cuenta1, cta_salida=cuenta2)
        self.cuenta1.dividir_entre(['subc1', 'sc1', 60], ['subc2', 'sc2'])
        mov.refresh_from_db()

        self.assertTrue(mov.tiene_cuenta_acumulativa())

    def test_tiene_cuenta_acumulativa_devuelve_false_si_mov_no_tiene_cuenta_acumulativa(self):
        cuenta2 = Cuenta.crear('cuenta2', 'c2')
        mov = Movimiento.crear(
            'traspaso', 100, cta_entrada=self.cuenta1, cta_salida=cuenta2)
        mov.refresh_from_db()
        self.assertFalse(mov.tiene_cuenta_acumulativa())

    def test_cambia_importe_devuelve_true_si_importe_es_distinto_del_guardado(self):
        mov = Movimiento.crear('entrada', 100, self.cuenta1)
        mov.importe = 200
        self.assertTrue(mov.cambia_importe())

    def test_cambia_importe_devuelve_false_si_importe_es_igual_al_guardado(self):
        mov = Movimiento.crear('entrada', 100, self.cuenta1)
        self.assertFalse(mov.cambia_importe())


class TestModelMovimientoSaldos(TestModelMovimiento):
    """ Saldos después de setUp:
        self.cuenta1: 125.0
        self.cuenta2: -35.0
    """

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear('Banco', 'B')
        self.saldo1 = self.cuenta1.saldo
        self.saldo2 = self.cuenta2.saldo
        self.mov1 = Movimiento.crear(
            fecha=date.today(),
            concepto='Carga de saldo',
            importe=125,
            cta_entrada=self.cuenta1
        )
        self.mov2 = Movimiento.crear(
            fecha=date.today(),
            concepto='Transferencia a otra cuenta',
            importe=35,
            cta_salida=self.cuenta2
        )

    def test_suma_importe_a_cta_entrada(self):
        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov1.importe)

    def test_resta_importe_de_cta_salida(self):
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov2.importe)

    def test_puede_traspasar_saldo_de_una_cuenta_a_otra(self):
        saldo1 = self.cuenta1.saldo
        saldo2 = self.cuenta2.saldo

        mov3 = Movimiento.crear(
            concepto='Depósito',
            importe=50,
            cta_entrada=self.cuenta2,
            cta_salida=self.cuenta1
        )
        self.assertEqual(self.cuenta2.saldo, saldo2+mov3.importe)
        self.assertEqual(self.cuenta1.saldo, saldo1-mov3.importe)


class TestModelMovimientoCambios(TestModelMovimiento):
    """ Saldos después de setUp:
        self.cuenta1: 125.0+50 = 175
        self.cuenta2: -35.0-50 = -85
    """

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear('Banco', 'B')
        self.mov1 = Movimiento.crear(
            fecha=date.today(),
            concepto='Carga de saldo',
            importe=125,
            cta_entrada=self.cuenta1
        )
        self.mov2 = Movimiento.crear(
            fecha=date.today(),
            concepto='Transferencia a otra cuenta',
            importe=35,
            cta_salida=self.cuenta2
        )
        self.mov3 = Movimiento.crear(
            concepto='Depósito',
            importe=50,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2
        )
        self.saldo1 = self.cuenta1.saldo
        self.saldo2 = self.cuenta2.saldo
        self.imp1 = self.mov1.importe
        self.imp2 = self.mov2.importe
        self.imp3 = self.mov3.importe

    def refresh_ctas(self, *args):
        self.cuenta1.refresh_from_db()
        self.cuenta2.refresh_from_db()
        for arg in args:
            arg.refresh_from_db()

    def test_eliminar_movimiento_resta_de_saldo_cta_entrada_y_suma_a_saldo_cta_salida(self):

        self.mov1.delete()
        self.cuenta1.refresh_from_db(fields=['_saldo'])

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp1)
        saldo1 = self.cuenta1.saldo

        self.mov3.delete()
        self.cuenta1.refresh_from_db(fields=['_saldo'])
        self.cuenta2.refresh_from_db(fields=['_saldo'])

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(self.cuenta1.saldo, saldo1-self.imp3)

    def test_modificar_movimiento_no_modifica_saldo_de_cuentas_si_no_se_modifica_importe_ni_cuentas(self):
        mov = Movimiento.tomar(concepto='Depósito')
        mov.concepto = 'Depósito en efectivo'
        mov.save()

        self.cuenta1.refresh_from_db()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2)

    def test_modificar_importe_resta_importe_antiguo_y_suma_el_nuevo_a_cta_entrada(self):
        self.mov1.importe = 128
        self.mov1.save()
        self.cuenta1.refresh_from_db()
        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1+self.mov1.importe)

    def test_modificar_importe_suma_importe_antiguo_y_resta_el_nuevo_a_cta_salida(self):
        self.mov2.importe = 37
        self.mov2.save()
        self.cuenta2.refresh_from_db()
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp2-self.mov2.importe)

    def test_modificar_importe_en_mov_traspaso_actua_sobre_las_dos_cuentas(self):
        """ Resta importe antiguo y suma nuevo a cta_entrada
            Suma importe antiguo y resta nuevo a cta_salida"""
        self.mov3.importe = 60
        self.mov3.save()
        self.refresh_ctas()
        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3+self.mov3.importe)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3-self.mov3.importe)

    def test_modificar_cta_entrada_resta_importe_de_saldo_cuenta_anterior_y_lo_suma_a_cuenta_nueva(self):
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_modificar_cta_salida_suma_importe_a_saldo_cuenta_anterior_y_lo_resta_de_cuenta_nueva(self):
        self.mov2.cta_salida = self.cuenta1
        self.mov2.save()
        self.refresh_ctas()
        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov2.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov2.importe)

    def test_modificar_cta_entrada_funciona_en_movimientos_de_traspaso(self):
        """ Resta importe de cta_entrada vieja y lo suma a la nueva."""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)
        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)

    def test_modificar_cta_salida_funciona_en_movimientos_de_traspaso(self):
        """ Suma importe a cta_salida vieja y lo suma a la nueva"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        self.mov3.cta_salida = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)

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

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)
        self.assertEqual(cuenta4.saldo, saldo4-self.mov3.importe)

    def test_intercambiar_cuentas_resta_importe_x2_de_cta_entrada_y_lo_suma_a_cta_salida(self):
        """ Resta dos veces importe de vieja cta_entrada (ahora cta_salida)
            Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov3.cta_salida = self.cuenta1
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2 + self.mov3.importe*2)
        self.assertEqual(self.cuenta1.saldo, self.saldo1 - self.mov3.importe*2)

    def test_cuenta_de_salida_pasa_a_ser_de_entrada(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, self.saldo2 + self.mov2.importe*2)

    def test_cuenta_de_entrada_pasa_a_ser_de_salida(self):
        """ Resta dos veces importe a vieja cta_entrada (ahora cta_salida)"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1 - self.mov1.importe*2)

    def test_cuenta_de_salida_pasa_a_ser_de_entrada_y_cuenta_nueva_de_salida(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)
            Resta importe de nueva cta_salida"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe*2)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)

    def test_cuenta_de_entrada_pasa_a_ser_de_salida_y_cuenta_nueva_de_entrada(self):
        """ Resta dos veces importe a vieja cta_entrada (ahora cta_salida
            Suma importe a nueva cta_entrada """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe*2)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)

    def test_cuenta_de_salida_desaparece(self):
        """ Suma importe a cta_salida retirada"""
        self.mov3.cta_salida = None
        self.mov3.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)

    def test_cuenta_de_entrada_desaparece(self):
        """ Resta importe a cta_entrada retirada"""
        self.mov3.cta_entrada = None
        self.mov3.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida(self):
        """ Suma importe a cta_salida retirada
            Resta dos veces a vieja cta_entrada (ahora cta_salida) """
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe*2)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada(self):
        """ Resta importe a cta_entrada retirada
            Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe*2)

    def test_aparece_cuenta_de_salida(self):
        """ Resta importe de nueva cta_salida """
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_aparece_cuenta_de_entrada(self):
        """ Suma importe a nueva cta_entrada """
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada(self):
        """ Resta dos veces importe de vieja cta_entrada (ahora cta_salida)
            Suma importe a nueva cta_entrada"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov1.importe*2)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)
            Resta importe de nueva cta_salida """
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta1
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov2.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov2.importe*2)

    def test_desaparece_cta_entrada_y_aparece_cta_de_salida(self):
        """ Resta importe de cta_entrada retirada
            Resta importe de cta_salida agregada """
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_desaparece_cta_salida_y_aparece_cta_de_entrada(self):
        """ Suma importe a cta_salida retirada
            Suma importe a cta_entrada agregada"""
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.cta_salida = None
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov2.importe)

    def test_cambia_cuenta_de_entrada_con_nuevo_importe(self):
        """ Resta viejo importe de cta_entrada vieja
            Suma nuevo importe a cta_entrada nueva """
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 128
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cambia_cuenta_de_salida_con_nuevo_importe(self):
        """ Suma viejo importe a cta_salida vieja
            Resta nuevo importe de cta_salida nueva """
        self.mov2.cta_salida = self.cuenta1
        self.mov2.importe = 63
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov2.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp2)

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

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)
        self.assertEqual(
            self.cuenta2.saldo,
            self.saldo2+self.imp3-self.mov3.importe
        )

    def test_cambia_cuenta_de_salida_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida vieja
            Resta importe nuevo de cta_salida nueva
            Resta importe viejo y suma importe nuevo a cta_entrada """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)
        self.assertEqual(
            self.cuenta1.saldo,
            self.saldo1-self.imp3+self.mov3.importe
        )

    def test_cambian_ambas_cuentas_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Resta importe viejo de cta_entrada vieja
            Suma importe nuevo a cta_entrada nueva
            Suma importe viejo a cta_salida vieja
            Suma importe nuevo a cta_entrada nueva """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        cuenta4 = Cuenta.crear('Colchón', 'ch')
        saldo4 = cuenta4.saldo

        self.mov3.cta_entrada = cuenta3
        self.mov3.cta_salida = cuenta4
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3, cuenta4)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)
        self.assertEqual(cuenta4.saldo, saldo4-self.mov3.importe)

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
            self.cuenta1.saldo, self.saldo1-self.imp3-self.mov3.importe)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3+self.mov3.importe)

    def test_cta_entrada_pasa_a_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a cta_entrada vieja
                (ahora cta_salida)"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.importe = 128
        self.mov1.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1-self.mov1.importe)

    def test_cta_salida_pasa_a_entrada_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada) """
        # self.cuenta1.saldo = 175
        # self.cuenta2.saldo = -85
        # self.mov2.importe = 35
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.importe = 128
        self.mov2.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp2+self.mov2.importe)

    def test_cta_salida_pasa_entrada_y_cta_salida_nueva_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada)
            Resta importe viejo de cta_entrada vieja
            Suma importe nuevo a cta_entrada nueva """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 252
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3+self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)

    def test_cta_entrada_pasa_salida_y_cta_entrada_nueva_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a cta_entrada vieja
                (ahora cta_salida)
            Resta importe viejo de cta_salida vieja
            Suma importe nuevo a cta_entrada nueva"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta3
        self.mov3.importe = 165
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)

    def test_cuenta_de_salida_desaparece_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida retirada
            Resta importe viejo y suma importe nuevo a cta_entrada"""
        self.mov3.cta_salida = None
        self.mov3.importe = 234
        self.mov3.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3+self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)

    def test_cuenta_de_entrada_desaparece_con_nuevo_importe(self):
        """ Resta importe viejo a cta_entrada retirada
            Suma importe viejo y resta importe nuevo a cta_salida"""
        self.mov3.cta_entrada = None
        self.mov3.importe = 234
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3-self.mov3.importe)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a vieja cta_entrada
                (ahora cta_salida)
            Suma importe viejo a cta_salida retirada """
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.importe = 350
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a vieja cta_salida
                (ahora cta_entrada)
            Resta importe viejo a cta_entrada retirada """
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.importe = 354
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3+self.mov3.importe)

    def test_aparece_cuenta_de_salida_con_nuevo_importe(self):
        """ Resta importe viejo y suma importe nuevo a cta_entrada
            Resta importe nuevo a cta_salida nueva"""
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 255
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1+self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_aparece_cuenta_de_entrada_con_nuevo_importe(self):
        """ Suma importe viejo y resta importe nuevo a cta_salida
            Suma importe nuevo a cta_entrada nueva"""
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.importe = 446
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp2-self.mov2.importe)

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo de antigua cta_entrada
                (ahora cta_salida)
            Suma importe nuevo a cta_entrada agregada"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 556
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1-self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo de antigua cta_salida
                (ahora cta_entrada)
            Resta importe nuevo de cta_salida nueva """
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta1
        self.mov2.importe = 445
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov2.importe)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp2+self.mov2.importe)

    def test_desaparece_cta_entrada_y_aparece_otra_cta_de_salida_con_nuevo_importe(self):
        """ Resta importe viejo de cta_entrada retirada
            Resta importe nuevo de cta_salida agregada """
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 565
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_desaparece_cta_salida_y_aparece_otra_cta_de_entrada_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida retirada
            Suma importe nuevo a cta_entrada agregada """
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.cta_salida = None
        self.mov2.importe = 675
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp2)


class TestModelMovimientoCuentas(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear('cuenta2', 'c2')

        self.entrada = Movimiento.crear(
            'entrada', 400, self.cuenta1, fecha=date(2021, 1, 5))
        self.salida = Movimiento.crear('salida', 200, None, self.cuenta1)
        self.trans_e = Movimiento.crear(
            'trans entrada acum', 200, self.cuenta1, self.cuenta2)
        self.trans_s = Movimiento.crear(
            'trans salida acum', 200, self.cuenta2, self.cuenta1)

        self.cuenta1 = dividir_en_dos_subcuentas(self.cuenta1)
        for mov in (self.entrada, self.salida, self.trans_e, self.trans_s):
            mov.refresh_from_db()

    def test_no_puede_modificarse_importe_de_movimiento_con_cta_entrada_acumulativa(self):
        self.entrada.importe = 300
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.entrada.full_clean()

    def test_no_puede_modificarse_importe_de_movimiento_con_cta_salida_acumulativa(self):
        self.salida.importe = 300
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.salida.full_clean()

    def test_no_puede_modificarse_importe_de_mov_de_traspaso_con_una_cuenta_acumulativa(self):
        self.trans_s.importe = 500
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.trans_s.full_clean()

        self.trans_e.importe = 500
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.trans_e.full_clean()

    def test_no_puede_modificarse_importe_de_mov_de_traspaso_con_ambas_cuentas_acumulativa(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )

        self.trans_e.importe = 600
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.trans_e.full_clean()

    def test_no_puede_retirarse_cta_entrada_de_movimiento_si_es_acumulativa(self):
        self.entrada.cta_entrada = self.cuenta2
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.entrada.full_clean()

    def test_no_puede_retirarse_cta_salida_de_movimiento_si_es_acumulativa(self):
        self.salida.cta_salida = self.cuenta2
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.salida.full_clean()

    def test_no_puede_retirarse_cuenta_de_traspaso_si_es_acumulativa(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3')
        self.trans_s.cta_salida = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.trans_s.full_clean()

        self.trans_e.cta_entrada = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.trans_e.full_clean()

    def test_no_puede_retirarse_cuenta_de_traspaso_si_ambas_son_acumulativas(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3')
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )

        self.trans_e.cta_entrada = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.trans_e.full_clean()

        self.trans_s.cta_salida = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.trans_s.full_clean()

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
            self.entrada.delete()

    def test_puede_modificarse_concepto_en_movimiento_de_entrada_con_cuenta_acumulativa(self):
        self.entrada.concepto = 'entrada cambiada'
        self.entrada.full_clean()
        self.entrada.save()
        self.assertEqual(self.entrada.concepto, 'entrada cambiada')

    def test_puede_modificarse_concepto_en_movimiento_de_salida_con_cuenta_acumulativa(self):
        self.salida.concepto = 'salida cambiada'
        self.salida.full_clean()
        self.salida.save()
        self.assertEqual(
            self.salida.concepto, 'salida cambiada')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_entrada(self):
        self.trans_e.concepto = 'entrada cambiada en traspaso'
        self.trans_e.full_clean()
        self.trans_e.save()
        self.assertEqual(
            self.trans_e.concepto, 'entrada cambiada en traspaso')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_salida(self):
        self.trans_s.concepto = 'salida cambiada en traspaso'
        self.trans_s.full_clean()
        self.trans_s.save()
        self.assertEqual(
            self.trans_s.concepto, 'salida cambiada en traspaso')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_ambas_cuentas_acumulativas(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )
        self.trans_s.concepto = 'concepto cambiado en traspaso'
        self.trans_s.full_clean()
        self.trans_s.save()
        self.assertEqual(
            self.trans_s.concepto, 'concepto cambiado en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_entrada_con_cuenta_acumulativa(self):
        self.entrada.detalle = 'entrada cambiada'
        self.entrada.full_clean()
        self.entrada.save()
        self.assertEqual(self.entrada.detalle, 'entrada cambiada')

    def test_puede_modificarse_detalle_en_movimiento_de_salida_con_cuenta_acumulativa(self):
        self.salida.detalle = 'salida cambiada'
        self.salida.full_clean()
        self.salida.save()
        self.assertEqual(
            self.salida.detalle, 'salida cambiada')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_entrada(self):
        self.trans_e.detalle = 'entrada cambiada en traspaso'
        self.trans_e.full_clean()
        self.trans_e.save()
        self.assertEqual(
            self.trans_e.detalle, 'entrada cambiada en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_salida(self):
        self.trans_s.detalle = 'salida cambiada en traspaso'
        self.trans_s.full_clean()
        self.trans_s.save()
        self.assertEqual(
            self.trans_s.detalle, 'salida cambiada en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_ambas_cuentas_acumulativas(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )
        self.trans_s.detalle = 'detalle cambiado en traspaso'
        self.trans_s.full_clean()
        self.trans_s.save()
        self.assertEqual(
            self.trans_s.detalle, 'detalle cambiado en traspaso')

    def test_puede_modificarse_fecha_en_movimiento_con_cta_entrada_acumulativa_si_fecha_es_anterior_a_conversion(self):
        self.entrada.fecha = date(2020, 1, 5)
        self.entrada.full_clean()
        self.entrada.save()
        self.assertEqual(self.entrada.fecha, date(2020, 1, 5))

    def test_puede_modificarse_fecha_en_movimiento_con_cta_salida_acumulativa_si_fecha_es_anterior_a_conversion(self):
        self.salida.fecha = date(2020, 1, 5)
        self.salida.full_clean()
        self.salida.save()
        self.assertEqual(self.salida.fecha, date(2020, 1, 5))

    def test_no_puede_asignarse_fecha_posterior_a_conversion_en_mov_con_cta_entrada_acumulativa(self):
        self.entrada.fecha = date.today() + timedelta(days=2)
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                f'{errors.FECHA_POSTERIOR_A_CONVERSION}{date.today()}'
        ):
            self.entrada.full_clean()

    def test_no_puede_asignarse_fecha_posterior_a_conversion_en_mov_con_cta_salida_acumulativa(self):
        self.salida.fecha = date.today() + timedelta(days=2)
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                f'{errors.FECHA_POSTERIOR_A_CONVERSION}{date.today()}'
        ):
            self.salida.full_clean()

    def test_puede_agregarse_contracuenta_interactiva_a_entrada_con_cta_acumulativa(self):
        self.entrada.cta_salida = self.cuenta2
        self.entrada.full_clean()
        self.entrada.save()
        self.assertEqual(self.entrada.cta_salida, self.cuenta2)

    def test_puede_agregarse_contracuenta_interactiva_a_salida_con_cta_acumulativa(self):
        self.salida.cta_entrada = self.cuenta2
        self.salida.full_clean()
        self.salida.save()
        self.assertEqual(self.salida.cta_entrada, self.cuenta2)

    def test_puede_modificarse_cta_interactiva_en_movimiento_con_cta_entrada_acumulativa(self):
        self.trans_e.cta_salida = self.cuenta2
        self.trans_e.full_clean()
        self.trans_e.save()
        self.assertEqual(self.trans_e.cta_salida, self.cuenta2)

    def test_puede_modificarse_cta_interactiva_en_movimiento_con_cta_salida_acumulativa(self):
        self.trans_s.cta_entrada = self.cuenta2
        self.trans_s.full_clean()
        self.trans_s.save()
        self.assertEqual(self.trans_s.cta_entrada, self.cuenta2)

    def test_puede_retirarse_cta_interactiva_en_movimiento_con_cta_entrada_acumulativa(self):
        self.trans_e.cta_salida = None
        self.trans_e.full_clean()
        self.trans_e.save()
        self.assertIsNone(self.trans_e.cta_salida)

    def test_puede_retirarse_cta_interactiva_en_movimiento_con_cta_salida_acumulativa(self):
        self.trans_s.cta_entrada = None
        self.trans_s.full_clean()
        self.trans_s.save()
        self.assertIsNone(self.trans_s.cta_entrada)
