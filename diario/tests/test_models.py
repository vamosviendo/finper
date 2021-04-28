from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.datetime_safe import date

from diario.models import Cuenta, Movimiento
from utils import errors


class TestModelCuenta(TestCase):

    def test_guarda_y_recupera_cuentas(self):
        primera_cuenta = Cuenta()
        primera_cuenta.nombre = 'Efectivo'
        primera_cuenta.slug = 'E'
        primera_cuenta.save()

        segunda_cuenta = Cuenta()
        segunda_cuenta.nombre = 'Caja de ahorro'
        segunda_cuenta.slug = 'CA'
        segunda_cuenta.save()

        cuentas_guardadas = Cuenta.objects.all()
        self.assertEqual(cuentas_guardadas.count(), 2)

        primera_cuenta_guardada = cuentas_guardadas[0]
        segunda_cuenta_guardada = cuentas_guardadas[1]
        self.assertEqual(primera_cuenta_guardada.nombre, 'Efectivo')
        self.assertEqual(primera_cuenta_guardada.slug, 'E')
        self.assertEqual(segunda_cuenta_guardada.nombre, 'Caja de ahorro')
        self.assertEqual(segunda_cuenta_guardada.slug, 'CA')

    def test_cuenta_creada_tiene_saldo_cero(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E')
        cuenta.save()
        self.assertEqual(cuenta.saldo, 0)

    def test_no_permite_nombres_duplicados(self):
        Cuenta.objects.create(nombre='Efectivo', slug='E')
        with self.assertRaises(ValidationError):
            cuenta2 = Cuenta(nombre='Efectivo', slug='EF')
            cuenta2.full_clean()

    def test_no_permite_slugs_duplicados(self):
        Cuenta.objects.create(nombre='Caja de ahorro', slug='CA')
        with self.assertRaises(ValidationError):
            cuenta2 = Cuenta(nombre='Cuenta de ahorro', slug='CA')
            cuenta2.full_clean()

    def test_no_permite_slug_vacio(self):
        with self.assertRaises(ValidationError):
            cuenta = Cuenta(nombre='Efectivo')
            cuenta.full_clean()

    def test_slug_se_guarda_siempre_en_mayusculas(self):
        Cuenta.crear(nombre='Efectivo', slug='Efec')
        cuenta = Cuenta.objects.first()
        self.assertEqual(cuenta.slug, 'EFEC')

    def test_cuenta_str(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E')
        self.assertEqual(str(cuenta), 'Efectivo')

    def test_crear_crea_cuenta(self):
        Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual(Cuenta.objects.count(), 1)

    def test_crear_devuelve_cuenta_creada(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual((cuenta.nombre, cuenta.slug), ('Efectivo', 'E'))

    def test_crear_valida_nombre_vacio(self):
        with self.assertRaises(ValidationError):
            Cuenta.crear(nombre=None, slug='E')


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

    def test_movimiento_str(self):
        cta1 = Cuenta.objects.create(nombre='Efectivo', slug='E')
        cta2 = Cuenta.objects.create(nombre='Banco', slug='B')
        mov1 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Retiro de efectivo',
            importe='250.2',
            cta_entrada=cta1,
            cta_salida=cta2
        )
        mov2 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Carga de saldo',
            importe='500',
            cta_entrada=cta1,
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
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        mov = Movimiento.objects.create(
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=cuenta
        )
        self.assertEqual(mov.fecha, date.today())

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
        cuenta1 = Cuenta.objects.create(nombre='Efectivo', slug='E')
        cuenta2 = Cuenta.objects.create(nombre='Banco', slug='B')
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
                ValidationError, errors.CUENTA_INEXISTENTE
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
        with self.assertRaisesMessage(ValidationError, errors.CUENTAS_IGUALES):
            mov.full_clean()

    def test_suma_importe_a_cta_entrada(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='Carga de saldo',
            importe=125.5,
            cta_entrada=cuenta
        )
        self.assertEqual(cuenta.saldo, 125.5)

    def test_resta_importe_de_cta_salida(self):
        cuenta = Cuenta.objects.create(nombre='Banco')
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='Transferencia a otra cuenta',
            importe=35.35,
            cta_salida=cuenta
        )
        self.assertEqual(cuenta.saldo, -35.35)

    def test_puede_traspasar_saldo_de_una_cuenta_a_otra(self):
        cta1 = Cuenta.objects.create(nombre='Efectivo', slug='E')
        cta2 = Cuenta.objects.create(nombre='Banco', slug='B')
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='Carga de saldo',
            importe=1535,
            cta_entrada=cta1
        )
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='Depósito',
            importe=830.25,
            cta_entrada=cta2,
            cta_salida=cta1
        )
        self.assertEqual(cta2.saldo, 830.25)
        self.assertEqual(cta1.saldo, 704.75)
