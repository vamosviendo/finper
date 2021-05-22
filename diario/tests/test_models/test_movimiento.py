from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento
from utils import errors


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
            '2021-03-22 Retiro de efectivo: 250.2 +Efectivo -Banco'
        )
        self.assertEqual(
            str(mov2),
            '2021-03-22 Carga de saldo: 500 +Efectivo'
        )
        self.assertEqual(
            str(mov3),
            '2021-03-22 Transferencia: 300.35 -Banco'
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

    def test_movimientos_se_ordenan_por_concepto_dentro_de_misma_fecha(self):
        mov1 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Pago en efectivo',
            importe=100,
            cta_salida=self.cuenta1,
        )
        mov2 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
        )
        mov3 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Pago a cuenta',
            importe=243,
            cta_entrada=self.cuenta1,
        )

        self.assertEqual(list(Movimiento.todes()), [mov2, mov3, mov1])


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



class TestModelMovimientoSaldos(TestModelMovimiento):

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
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)
        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)

    def test_modificar_cta_salida_funciona_en_movimientos_de_traspaso(self):
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        self.mov3.cta_salida = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)

    def test_modificar_ambas_cuentas_funciona_en_movimientos_de_traspaso(self):
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
        self.mov3.cta_salida = self.cuenta1
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2 + self.mov3.importe*2)
        self.assertEqual(self.cuenta1.saldo, self.saldo1 - self.mov3.importe*2)

    def test_cuenta_de_salida_pasa_a_ser_de_entrada(self):
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, self.saldo2 + self.mov2.importe*2)

    def test_cuenta_de_entrada_pasa_a_ser_de_salida(self):
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1 - self.mov1.importe*2)

    def test_cuenta_de_salida_pasa_a_ser_de_entrada_y_cuenta_nueva_de_salida(self):
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
        self.mov3.cta_salida = None
        self.mov3.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)

    def test_cuenta_de_entrada_desaparece(self):
        self.mov3.cta_entrada = None
        self.mov3.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida(self):
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe*2)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada(self):
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe*2)

    def test_aparece_cuenta_de_salida(self):
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_aparece_cuenta_de_entrada(self):
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada(self):
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov1.importe*2)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida(self):
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta1
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov2.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov2.importe*2)

    def test_desaparece_cta_entrada_y_aparece_otra_cta_de_salida(self):
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_desaparece_cta_salida_y_aparece_otra_cta_de_entrada(self):
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.cta_salida = None
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov2.importe)

    def test_cambia_cuenta_de_entrada_con_nuevo_importe(self):
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 128
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cambia_cuenta_de_salida_con_nuevo_importe(self):
        self.mov2.cta_salida = self.cuenta1
        self.mov2.importe = 63
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov2.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp2)

    def test_cambia_cuenta_de_entrada_en_mov_de_traspaso_con_nuevo_importe(self):
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_entrada = cuenta3
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)

    def test_cambia_cuenta_de_salida_en_mov_de_traspaso_con_nuevo_importe(self):
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)

    def test_cambian_ambas_cuentas_en_mov_de_traspaso_con_nuevo_importe(self):
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
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.importe = 128
        self.mov1.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1-self.mov1.importe)

    def test_cta_salida_pasa_a_entrada_con_nuevo_importe(self):
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.importe = 128
        self.mov2.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp2+self.mov2.importe)

    def test_cta_salida_pasa_entrada_y_cta_salida_nueva_con_nuevo_importe(self):
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
        self.mov3.cta_salida = None
        self.mov3.importe = 234
        self.mov3.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3+self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)

    def test_cuenta_de_entrada_desaparece_con_nuevo_importe(self):
        self.mov3.cta_entrada = None
        self.mov3.importe = 234
        self.mov3.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3-self.mov3.importe)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida_con_nuevo_importe(self):
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.importe = 350
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada_con_nuevo_importe(self):
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.importe = 354
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3+self.mov3.importe)

    def test_aparece_cuenta_de_salida_con_nuevo_importe(self):
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 255
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1+self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_aparece_cuenta_de_entrada_con_nuevo_importe(self):
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.importe = 446
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp2-self.mov2.importe)

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada_con_nuevo_importe(self):
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 556
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1-self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida_con_nuevo_importe(self):
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta1
        self.mov2.importe = 445
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov2.importe)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp2+self.mov2.importe)

    def test_desaparece_cta_entrada_y_aparece_otra_cta_de_salida_con_nuevo_importe(self):
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 565
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_desaparece_cta_salida_y_aparece_otra_cta_de_entrada_con_nuevo_importe(self):
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
        self.cuenta1.dividir_entre([
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 0},
            {'nombre': 'Cajón', 'slug': 'ecaj', 'saldo': 0},
        ])

    def test_movimiento_no_acepta_cuenta_no_interactiva(self):
        with self.assertRaises(ValidationError):
            Movimiento.crear(
                concepto='mov', importe=100, cta_entrada=self.cuenta1)
