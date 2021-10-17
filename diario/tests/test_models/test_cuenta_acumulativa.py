from datetime import date

from django.test import TestCase

from diario.models import Cuenta, Movimiento, Titular
from utils.errors import ErrorCuentaEsAcumulativa, \
    CUENTA_ACUMULATIVA_EN_MOVIMIENTO
from utils.helpers_tests import dividir_en_dos_subcuentas


class TestCuentaAcumulativa(TestCase):

    def setUp(self):
        self.cta_acum = Cuenta.crear('cta acum', 'ca')
        self.cta_int = Cuenta.crear('cta int', 'ci')
        Movimiento.crear('entrada', 200, cta_entrada=self.cta_acum)
        Movimiento.crear('salida', 100, cta_salida=self.cta_acum)
        self.cta_acum = dividir_en_dos_subcuentas(self.cta_acum, saldo=100)

    def test_cuenta_acumulativa_no_puede_participar_en_movimientos_nuevos(self):
        with self.assertRaisesMessage(
                ErrorCuentaEsAcumulativa, CUENTA_ACUMULATIVA_EN_MOVIMIENTO):
            Movimiento.crear(
                'movimiento sobre acum', 100, cta_entrada=self.cta_acum)

    def test_guarda_en_campo_fecha_conversion_dia_en_que_se_convirtio_en_acumulativa(self):
        fecha = date.today()
        cta_acum = self.cta_int.dividir_y_actualizar(
            ['subi1', 'si1', 0], ['subi2', 'si2']
        )
        self.assertEqual(cta_acum.fecha_conversion, fecha)


class TestTitulares(TestCase):

    def setUp(self):
        self.cta_acum = Cuenta.crear('cta acum', 'ca')
        Movimiento.crear('entrada', 200, cta_entrada=self.cta_acum)
        Movimiento.crear('salida', 100, cta_salida=self.cta_acum)
        self.cta_acum = dividir_en_dos_subcuentas(self.cta_acum, saldo=100)
        self.subcuentas = list(self.cta_acum.subcuentas.all())
        self.tit1 = Titular.crear(titname='titi', nombre='Titi Títez')
        self.tit2 = Titular.crear(titname='joji', nombre='Joji Jújez')

    def test_devuelve_lista_de_titulares_de_subcuentas(self):
        self.subcuentas[0].titular = self.tit1
        self.subcuentas[0].save()
        self.subcuentas[1].titular = self.tit2
        self.subcuentas[1].save()

        self.assertEqual(self.cta_acum.titulares, [self.tit1, self.tit2])

    def test_no_incluye_titulares_repetidos(self):
        self.cta_acum.agregar_subcuenta(['subcuenta 3', 'sc3'])
        self.subcuentas.append(Cuenta.tomar(slug='sc3'))
        self.subcuentas[0].titular = self.tit1
        self.subcuentas[0].save()
        self.subcuentas[1].titular = self.tit2
        self.subcuentas[1].save()
        self.subcuentas[2].titular = self.tit1
        self.subcuentas[2].save()

        self.assertEqual(self.cta_acum.titulares, [self.tit1, self.tit2])

    def test_si_subcuenta_es_acumulativa_incluye_titulares_de_subcuenta(self):
        self.subcuentas[1].titular = self.tit2
        self.subcuentas[1].save()

        self.subcuentas[0] = self.subcuentas[0].dividir_y_actualizar(
            ['subsubcuenta 1.1', 'sc11', 50],
            ['subsubcuenta 1.2', 'sc12']
        )
        tit3 = Titular.crear(titname='fufi', nombre='Fufi Fúfez')

        subsubcuentas = list(self.subcuentas[0].subcuentas.all())
        subsubcuentas[0].titular = self.tit1
        subsubcuentas[0].save()
        subsubcuentas[1].titular = tit3
        subsubcuentas[1].save()

        self.assertEqual(self.cta_acum.titulares, [self.tit1, self.tit2, tit3])


class TestAgregarSubcuenta(TestCase):

    def setUp(self):
        self.cta_acum = Cuenta.crear('cta acum', 'ca')
        Movimiento.crear('entrada', 200, cta_entrada=self.cta_acum)
        Movimiento.crear('salida', 100, cta_salida=self.cta_acum)
        self.cta_acum = dividir_en_dos_subcuentas(self.cta_acum, saldo=100)

    def test_agregar_subcuenta_crea_nueva_subcuenta(self):
        self.cta_acum.agregar_subcuenta(['subc3', 'sc3'])
        self.assertEqual(self.cta_acum.subcuentas.count(), 3)

    def test_subcuenta_agregadada_tiene_saldo_cero(self):
        self.cta_acum.agregar_subcuenta(['subc3', 'sc3'])
        subcuenta = Cuenta.tomar(slug='sc3')
        self.assertEqual(subcuenta.saldo, 0)


class TestSaldoOk(TestCase):

    def setUp(self):
        self.cta_acum = Cuenta.crear('cta acum', 'ca')
        Movimiento.crear('entrada', 200, cta_entrada=self.cta_acum)
        Movimiento.crear('salida', 100, cta_salida=self.cta_acum)
        self.cta_acum = dividir_en_dos_subcuentas(self.cta_acum, saldo=100)

    def test_saldo_ok_devuelve_true_si_saldo_coincide_con_saldos_subcuentas(self):
        self.assertEqual(self.cta_acum.saldo, self.cta_acum.total_subcuentas())
        self.assertTrue(self.cta_acum.saldo_ok())

    def test_saldo_ok_devuelve_false_si_saldo_no_coincide_con_saldos_subcuentas(self):
        cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=cta1,
            fecha=date(2019, 1, 1)
        )
        cta1 = cta1.dividir_y_actualizar(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 15},
            {'nombre': 'Cajón', 'slug': 'ec', }
        )
        cta1.saldo = 220
        cta1.save()

        self.assertFalse(cta1.saldo_ok())


class TestCorregirSaldo(TestCase):

    def test_corregir_saldo_corrige_a_partir_de_saldos_de_subcuentas(self):
        cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=cta1,
            fecha=date(2019, 1, 1)
        )
        cta1 = cta1.dividir_y_actualizar(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 15},
            {'nombre': 'Cajón', 'slug': 'ec', 'saldo': 65},
            {'nombre': 'Cajita', 'slug': 'eca', }
        )
        cta2 = Cuenta.tomar(slug='eb')
        Movimiento.crear('Movimiento', 5, cta_salida=cta2)
        cta1.saldo = 550
        cta1.save()
        cta1.corregir_saldo()
        cta1.refresh_from_db()
        self.assertEqual(cta1.saldo, cta1.total_subcuentas())
