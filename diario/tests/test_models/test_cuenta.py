from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento

from utils.errors import SaldoNoCeroException


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

        cuentas_guardadas = Cuenta.todes()
        self.assertEqual(cuentas_guardadas.count(), 2)

        primera_cuenta_guardada = Cuenta.tomar(pk=primera_cuenta.pk)
        segunda_cuenta_guardada = Cuenta.tomar(pk=segunda_cuenta.pk)

        self.assertEqual(primera_cuenta_guardada.nombre, 'Efectivo')
        self.assertEqual(primera_cuenta_guardada.slug, 'E')
        self.assertEqual(segunda_cuenta_guardada.nombre, 'Caja de ahorro')
        self.assertEqual(segunda_cuenta_guardada.slug, 'CA')

    def test_cuenta_creada_tiene_saldo_cero(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E')
        cuenta.save()
        self.assertEqual(cuenta.saldo, 0)

    def test_no_permite_nombres_duplicados(self):
        Cuenta.crear(nombre='Efectivo', slug='E')
        with self.assertRaises(ValidationError):
            cuenta2 = Cuenta(nombre='Efectivo', slug='EF')
            cuenta2.full_clean()

    def test_no_permite_slugs_duplicados(self):
        Cuenta.crear(nombre='Caja de ahorro', slug='CA')
        with self.assertRaises(ValidationError):
            cuenta2 = Cuenta(nombre='Cuenta de ahorro', slug='CA')
            cuenta2.full_clean()

    def test_no_permite_slug_vacio(self):
        with self.assertRaises(ValidationError):
            cuenta = Cuenta(nombre='Efectivo')
            cuenta.full_clean()

    def test_slug_se_guarda_siempre_en_mayusculas(self):
        Cuenta.crear(nombre='Efectivo', slug='Efec')
        cuenta = Cuenta.primere()
        self.assertEqual(cuenta.slug, 'EFEC')

    def test_cuenta_str(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E')
        self.assertEqual(str(cuenta), 'Efectivo')

    def test_crear_crea_cuenta(self):
        Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual(Cuenta.cantidad(), 1)

    def test_crear_devuelve_cuenta_creada(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual((cuenta.nombre, cuenta.slug), ('Efectivo', 'E'))

    def test_crear_no_permite_nombre_vacio(self):
        with self.assertRaises(ValidationError):
            Cuenta.crear(nombre=None, slug='E')

    def test_no_permite_eliminar_cuentas_con_saldo(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        Movimiento.crear(
            concepto='Saldo', importe=100, cta_entrada=cuenta)
        with self.assertRaises(SaldoNoCeroException):
            cuenta.delete()

    def test_cuentas_se_ordenan_por_nombre(self):
        cuenta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cuenta2 = Cuenta.crear(nombre='Banco', slug='ZZ')
        cuenta3 = Cuenta.crear(nombre='Cuenta Corriente', slug='CC')

        self.assertEqual(list(Cuenta.todes()), [cuenta2, cuenta3, cuenta1])


class TestModelCuentaMetodos(TestCase):

    def setUp(self):
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        self.cta2 = Cuenta.crear('Banco', 'B')
        Movimiento.crear(concepto='mov1', importe=100, cta_entrada=self.cta1)
        Movimiento.crear(
            concepto='mov2', importe=70,
            cta_entrada= self.cta2, cta_salida=self.cta1
        )
        Movimiento.crear(concepto='mov3', importe=80, cta_entrada=self.cta1)
        Movimiento.crear(concepto='mov4', importe=50, cta_entrada=self.cta2)

    def test_cantidad_movs_devuelve_entradas_mas_salidas(self):
        self.assertEqual(self.cta1.cantidad_movs(), 3)

    def test_total_movs_devuelve_suma_importes_entradas_menos_salidas(self):
        self.assertEqual(self.cta1.total_movs(), 110)

    def test_saldo_ok_devuelve_true_si_saldo_coincide_con_movimientos(self):
        self.assertEqual(self.cta1.saldo, 110)
        self.assertTrue(self.cta1.saldo_ok())

    def test_saldo_ok_devuelve_false_si_saldo_no_coincide_con_movimientos(self):
        self.cta1.saldo = 220
        self.cta1.save()
        self.assertFalse(self.cta1.saldo_ok())

    def test_corregir_saldo_corrige_saldo_a_partir_de_los_importes_de_movimientos(self):
        self.cta1.saldo = 345
        self.cta1.save()
        self.cta1.corregir_saldo()
        self.cta1.refresh_from_db()
        self.assertTrue(self.cta1.saldo_ok())

    def test_corregir_saldo_no_agrega_movimientos(self):
        self.cta1.saldo = 345
        self.cta1.save()
        entradas = self.cta1.entradas.count()
        salidas = self.cta1.salidas.count()
        self.cta1.corregir_saldo()
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.entradas.count(), entradas)
        self.assertEqual(self.cta1.salidas.count(), salidas)

    def test_agregar_mov_correctivo_agrega_un_movimiento(self):
        self.cta1.saldo = 880
        self.cta1.save()
        cant_movs = self.cta1.cantidad_movs()
        self.cta1.agregar_mov_correctivo()
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.cantidad_movs(), cant_movs+1)

    def test_agregar_mov_correctivo_devuelve_un_movimiento(self):
        self.cta1.saldo = 880
        self.cta1.save()
        self.assertIsInstance(self.cta1.agregar_mov_correctivo(), Movimiento)

    def test_importe_del_mov_correctivo_coincide_con_diferencia_con_saldo(self):
        self.cta1.saldo = 880
        self.cta1.save()
        mov = self.cta1.agregar_mov_correctivo()
        self.assertEqual(mov.importe, 770)

    def test_mov_correctivo_importe_es_siempre_positivo(self):
        self.cta2.saldo = 70
        self.cta2.save()
        mov = self.cta2.agregar_mov_correctivo()
        self.assertGreater(mov.importe, 0)

    def test_mov_correctivo_cuenta_es_de_entrada_o_salida_segun_signo_de_la_diferencia(self):
        self.cta1.saldo = 880
        self.cta1.save()
        mov1 = self.cta1.agregar_mov_correctivo()
        self.assertEqual(mov1.cta_entrada, self.cta1)

        self.cta2.saldo = 70
        self.cta2.save()
        mov2 = self.cta2.agregar_mov_correctivo()
        self.assertEqual(mov2.cta_salida, self.cta2)

    def test_mov_correctivo_no_modifica_saldo(self):
        self.cta1.saldo = 880
        self.cta1.save()
        mov1 = self.cta1.agregar_mov_correctivo()
        self.assertEqual(self.cta1.saldo, 880)

    def test_mov_correctivo_no_agrega_movimiento_si_saldo_es_correcto(self):
        cant_movs = self.cta1.cantidad_movs()
        mov = self.cta1.agregar_mov_correctivo()
        self.assertEqual(self.cta1.cantidad_movs(), cant_movs)
        self.assertIsNone(mov)
