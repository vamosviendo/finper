from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.datetime_safe import date

from diario.models import Cuenta, Movimiento
from utils import errors


class TestModelMovimiento(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.crear(nombre='Efectivo', slug='e')


class TestModelMovimientoBasic(TestModelMovimiento):

    def test_guarda_y_recupera_movimientos(self):
        primer_mov = Movimiento()
        primer_mov.fecha = date.today()
        primer_mov.concepto = 'entrada de efectivo'
        primer_mov.importe = 985.5
        primer_mov.cta_entrada = self.cuenta
        primer_mov.save()

        segundo_mov = Movimiento()
        segundo_mov.fecha = date(2021, 4, 5)
        segundo_mov.concepto = 'compra en efectivo'
        segundo_mov.detalle = 'salchichas, pan, mostaza'
        segundo_mov.importe = 500
        segundo_mov.cta_salida = self.cuenta
        segundo_mov.save()

        movs_guardados = Movimiento.todes()
        self.assertEqual(movs_guardados.count(), 2)

        primer_mov_guardado = movs_guardados[0]
        segundo_mov_guardado = movs_guardados[1]

        self.assertEqual(primer_mov_guardado.fecha, date.today())
        self.assertEqual(primer_mov_guardado.concepto, 'entrada de efectivo')
        self.assertEqual(primer_mov_guardado.importe, 985.5)
        self.assertEqual(primer_mov_guardado.cta_entrada, self.cuenta)

        self.assertEqual(segundo_mov_guardado.fecha, date(2021, 4, 5))
        self.assertEqual(segundo_mov_guardado.concepto, 'compra en efectivo')
        self.assertEqual(
            segundo_mov_guardado.detalle, 'salchichas, pan, mostaza')
        self.assertEqual(segundo_mov_guardado.importe, 500)
        self.assertEqual(segundo_mov_guardado.cta_salida, self.cuenta)

    def test_cta_entrada_se_relaciona_con_cuenta(self):
        mov = Movimiento(
            fecha=date.today(), concepto='Cobranza en efectivo', importe=100)
        mov.cta_entrada = self.cuenta
        mov.save()
        self.assertIn(mov, self.cuenta.entradas.all())

    def test_cta_salida_se_relaciona_con_cuenta(self):
        mov = Movimiento(
            fecha=date.today(), concepto='Cobranza en efectivo', importe=100)
        mov.cta_salida = self.cuenta
        mov.save()
        self.assertIn(mov, self.cuenta.salidas.all())

    def test_permite_guardar_cuentas_de_entrada_y_salida_en_un_movimiento(self):
        cuenta2 = Cuenta.crear(nombre='Banco', slug='B')
        mov = Movimiento(
            fecha=date.today(),
            concepto='Retiro de efectivo',
            importe=100,
            cta_entrada=self.cuenta,
            cta_salida=cuenta2
        )

        mov.full_clean()    # No debe dar error
        mov.save()

        self.assertIn(mov, self.cuenta.entradas.all())
        self.assertIn(mov, cuenta2.salidas.all())
        self.assertNotIn(mov, self.cuenta.salidas.all())
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
            cta_entrada=self.cuenta,
            cta_salida=self.cuenta
        )
        with self.assertRaisesMessage(ValidationError, errors.CUENTAS_IGUALES):
            mov.full_clean()

    def test_movimiento_str(self):
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        mov1 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Retiro de efectivo',
            importe='250.2',
            cta_entrada=self.cuenta,
            cta_salida=cta2
        )
        mov2 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Carga de saldo',
            importe='500',
            cta_entrada=self.cuenta,
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
            cta_entrada=self.cuenta
        )
        self.assertEqual(mov.fecha, date.today())

    def test_permite_movimientos_duplicados(self):
        Movimiento.crear(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta
        )
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta
        )
        mov.full_clean()    # No debe dar error


class TestModelMovimientoSaldos(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear('Banco', 'B')
        self.saldo1 = self.cuenta.saldo
        self.saldo2 = self.cuenta2.saldo
        self.mov1 = Movimiento.crear(
            fecha=date.today(),
            concepto='Carga de saldo',
            importe=125,
            cta_entrada=self.cuenta
        )
        self.mov2 = Movimiento.crear(
            fecha=date.today(),
            concepto='Transferencia a otra cuenta',
            importe=35,
            cta_salida=self.cuenta2
        )

    def test_suma_importe_a_cta_entrada(self):
        self.assertEqual(self.cuenta.saldo, self.saldo1+self.mov1.importe)

    def test_resta_importe_de_cta_salida(self):
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov2.importe)

    def test_puede_traspasar_saldo_de_una_cuenta_a_otra(self):
        saldo1 = self.cuenta.saldo
        saldo2 = self.cuenta2.saldo

        mov3 = Movimiento.crear(
            concepto='Depósito',
            importe=50,
            cta_entrada=self.cuenta2,
            cta_salida=self.cuenta
        )
        self.assertEqual(self.cuenta2.saldo, saldo2+mov3.importe)
        self.assertEqual(self.cuenta.saldo, saldo1-mov3.importe)


class TestModelMovimientoCambios(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear('Banco', 'B')
        self.mov1 = Movimiento.crear(
            fecha=date.today(),
            concepto='Carga de saldo',
            importe=125,
            cta_entrada=self.cuenta
        )
        self.mov2 = Movimiento.crear(
            fecha=date.today(),
            concepto='Transferencia a otra cuenta',
            importe=35,
            cta_salida=self.cuenta2
        )
        self.mov3 = Movimiento.crear(
            concepto='Depósito',
            importe=25,
            cta_entrada=self.cuenta2,
            cta_salida=self.cuenta
        )
        self.saldo1 = self.cuenta.saldo
        self.saldo2 = self.cuenta2.saldo
        self.imp1 = self.mov1.importe
        self.imp2 = self.mov2.importe
        self.imp3 = self.mov3.importe

    def test_eliminar_movimiento_resta_de_saldo_cta_entrada_y_suma_a_saldo_cta_salida(self):

        self.mov1.delete()
        self.cuenta.refresh_from_db(fields=['saldo'])

        self.assertEqual(self.cuenta.saldo, self.saldo1-self.imp1)
        saldo1 = self.cuenta.saldo

        self.mov3.delete()
        self.cuenta.refresh_from_db(fields=['saldo'])
        self.cuenta2.refresh_from_db(fields=['saldo'])

        self.assertEqual(self.cuenta.saldo, saldo1+self.imp3)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.imp3)

    def test_modificar_movimiento_no_modifica_saldo_de_cuentas_si_no_se_modifica_importe_ni_cuentas(self):
        mov = Movimiento.tomar(concepto='Depósito')
        mov.concepto = 'Depósito en efectivo'
        mov.save()

        self.cuenta.refresh_from_db()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta.saldo, self.saldo1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2)
