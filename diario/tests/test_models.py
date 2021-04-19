from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.datetime_safe import date

from diario.models import Cuenta, Movimiento


class TestModelCuenta(TestCase):

    def test_guarda_y_recupera_cuentas(self):
        primera_cuenta = Cuenta()
        primera_cuenta.nombre = 'Efectivo'
        primera_cuenta.save()

        segunda_cuenta = Cuenta()
        segunda_cuenta.nombre = 'Caja de ahorro'
        segunda_cuenta.save()

        cuentas_guardadas = Cuenta.objects.all()
        self.assertEqual(cuentas_guardadas.count(), 2)

        primera_cuenta_guardada = cuentas_guardadas[0]
        segunda_cuenta_guardada = cuentas_guardadas[1]
        self.assertEqual(primera_cuenta_guardada.nombre, 'Efectivo')
        self.assertEqual(segunda_cuenta_guardada.nombre, 'Caja de ahorro')

    def test_no_permite_cuentas_duplicadas(self):
        Cuenta.objects.create(nombre='Efectivo')
        with self.assertRaises(ValidationError):
            cuenta2 = Cuenta(nombre='Efectivo')
            cuenta2.full_clean()


class TestModelMovimiento(TestCase):

    def test_guarda_y_recupera_movimientos(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')

        primer_mov = Movimiento()
        primer_mov.fecha = date.today()
        primer_mov.concepto = 'entrada de efectivo'
        primer_mov.importe = 985.5
        primer_mov.cta_entrada = cuenta
        primer_mov.save()

        segundo_mov = Movimiento()
        segundo_mov.fecha = date(2021, 4, 5)
        segundo_mov.concepto = 'compra en efectivo'
        segundo_mov.detalle = 'salchichas, pan, mostaza'
        segundo_mov.importe = 500
        segundo_mov.cta_salida = cuenta
        segundo_mov.save()

        movs_guardados = Movimiento.objects.all()
        self.assertEqual(movs_guardados.count(), 2)

        primer_mov_guardado = movs_guardados[0]
        segundo_mov_guardado = movs_guardados[1]

        self.assertEqual(primer_mov_guardado.fecha, date.today())
        self.assertEqual(primer_mov_guardado.concepto, 'entrada de efectivo')
        self.assertEqual(primer_mov_guardado.importe, 985.5)
        self.assertEqual(primer_mov_guardado.cta_entrada, cuenta)

        self.assertEqual(segundo_mov_guardado.fecha, date(2021, 4, 5))
        self.assertEqual(segundo_mov_guardado.concepto, 'compra en efectivo')
        self.assertEqual(
            segundo_mov_guardado.detalle, 'salchichas, pan, mostaza')
        self.assertEqual(segundo_mov_guardado.importe, 500)
        self.assertEqual(segundo_mov_guardado.cta_salida, cuenta)

    def test_permite_movimientos_duplicados(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=cuenta
        )
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=cuenta
        )
        mov.full_clean()    # No debe dar error

    def test_cta_entrada_se_relaciona_con_cuenta(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        mov = Movimiento(
            fecha=date.today(), concepto='Cobranza en efectivo', importe=100)
        mov.cta_entrada = cuenta
        mov.save()
        self.assertIn(mov, cuenta.entradas.all())

    def test_cta_salida_se_relaciona_con_cuenta(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        mov = Movimiento(
            fecha=date.today(), concepto='Cobranza en efectivo', importe=100)
        mov.cta_salida = cuenta
        mov.save()
        self.assertIn(mov, cuenta.salidas.all())

    def test_permite_guardar_cuentas_de_entrada_y_salida_en_un_movimiento(self):
        cuenta1 = Cuenta.objects.create(nombre='Efectivo')
        cuenta2 = Cuenta.objects.create(nombre='Banco')
        mov = Movimiento(
            fecha=date.today(),
            concepto='Retiro de efectivo',
            importe=100,
            cta_entrada=cuenta1,
            cta_salida=cuenta2
        )

        mov.full_clean()    # No debe dar error
        mov.save()

        self.assertIn(mov, cuenta1.entradas.all())
        self.assertIn(mov, cuenta2.salidas.all())
        self.assertNotIn(mov, cuenta1.salidas.all())
        self.assertNotIn(mov, cuenta2.entradas.all())

    def test_requiere_al_menos_una_cuenta(self):
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100
        )
        with self.assertRaisesMessage(
                ValidationError,
                'Debe haber una cuenta de entrada, una de salida o ambas.'
        ):
            mov.full_clean()

    def test_no_admite_misma_cuenta_de_entrada_y_de_salida(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=cuenta,
            cta_salida=cuenta
        )
        with self.assertRaisesMessage(
                ValidationError, 'Cuentas de entrada y salida no pueden ser la misma.'):
            mov.full_clean()
