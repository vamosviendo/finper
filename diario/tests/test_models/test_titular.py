from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Titular, CuentaInteractiva, Cuenta, Movimiento
from diario.settings_app import TITULAR_PRINCIPAL
from utils.helpers_tests import dividir_en_dos_subcuentas


class TestModelTitular(TestCase):

    def setUp(self):
        for tit in Titular.todes():
            tit.delete()

    def test_guarda_y_recupera_titulares(self):
        titular = Titular()
        titular.titname = "juan"
        titular.nombre = 'Juan Juánez'
        titular.full_clean()
        titular.save()

        self.assertEqual(Titular.cantidad(), 1)
        tit = Titular.tomar(titname="juan")
        self.assertEqual(tit.nombre, "Juan Juánez")

    def test_no_admite_titulares_sin_titname(self):
        titular = Titular(nombre='Juan Juánez')
        with self.assertRaises(ValidationError):
            titular.full_clean()

    def test_no_admite_titulares_con_el_mismo_titname(self):
        Titular.crear(titname='juan', nombre='Juan Juánez')
        titular2 = Titular(titname='juan', nombre='Juan Juánez')

        with self.assertRaises(ValidationError):
            titular2.full_clean()

    def test_si_no_se_proporciona_nombre_toma_titname_como_nombre(self):
        titular = Titular(titname='juan')
        titular.full_clean()

        titular.save()
        tit = Titular.tomar(titname='juan')

        self.assertEqual(tit.nombre, 'juan')

    def test_se_relaciona_con_cuentas(self):
        titular = Titular.crear(titname='juan')
        cuenta = CuentaInteractiva(nombre='cuenta', slug='cta')
        cuenta.titular = titular
        cuenta.full_clean()
        cuenta.save()

        self.assertIn(cuenta, titular.cuentas.all())

    def test_str_devuelve_nombre_titular(self):
        titular = Titular.crear(titname='juan', nombre='Juan Juanínez')
        self.assertEqual(str(titular), 'Juan Juanínez')


class TestTitularPatrimonio(TestCase):

    def test_devuelve_suma_de_saldos_de_cuentas_de_titular(self):
        tit = Titular.crear(titname='Titu')
        CuentaInteractiva.crear('cuenta1', 'cta1', saldo=500, titular=tit)
        CuentaInteractiva.crear('cuenta2', 'cta2', saldo=-120, titular=tit)
        CuentaInteractiva.crear('cuenta_ajena', 'ctaj', saldo=300)

        self.assertEqual(tit.patrimonio, 380)

    def test_funciona_correctamente_con_valores_con_decimales(self):
        tit = Titular.crear(titname='Titu')
        CuentaInteractiva.crear('cuenta1', 'cta1', saldo=500.22, titular=tit)
        CuentaInteractiva.crear('cuenta2', 'cta2', saldo=-120.35, titular=tit)

        self.assertEqual(tit.patrimonio, round(500.22-120.35, 2))

    def test_devuelve_cero_si_titular_no_tiene_cuentas(self):
        tit = Titular.crear(titname='Toti')
        self.assertEqual(tit.patrimonio, 0)


class TestTitularMovimientos(TestCase):

    def setUp(self):
        self.tit = Titular.crear(titname='tito', nombre='Tito Gómez')
        self.cuenta1 = Cuenta.crear(nombre='cuenta1', slug='cta1', titular=self.tit)
        self.cuenta2 = Cuenta.crear(nombre='cuenta2', slug='cta2')
        self.mov1 = Movimiento.crear('Movimiento 1', 120, self.cuenta1)
        self.mov2 = Movimiento.crear('Movimiento 2', 65, None, self.cuenta2)
        self.mov3 = Movimiento.crear('Movimiento 3', 35, self.cuenta1, self.cuenta2)

    def test_devuelve_movimientos_relacionados_con_cuentas_del_titular(self):
        self.assertEqual(self.tit.movimientos(), [self.mov1, self.mov3])

    def test_no_incluye_movimientos_no_relacionados_con_cuentas_del_titular(self):
        self.assertNotIn(self.mov2, self.tit.movimientos())

    def test_incluye_movimientos_de_cuentas_convertidas_en_acumulativas(self):
        dividir_en_dos_subcuentas(self.cuenta1, saldo=15)
        self.assertIn(self.mov1, self.tit.movimientos())


class TestMetodoPorDefecto(TestCase):

    def setUp(self):
        for tit in Titular.todes():
            tit.delete()

    def test_devuelve_pk_de_titular_principal(self):
        titular_principal = Titular.crear(
            titname=TITULAR_PRINCIPAL['titname'],
            nombre=TITULAR_PRINCIPAL['nombre']
        )
        self.assertEqual(
            Titular.por_defecto(),
            titular_principal.pk
        )

    def test_crea_titular_principal_si_no_existe(self):
        pk_titular_principal = Titular.por_defecto()
        self.assertEqual(Titular.cantidad(), 1)
        self.assertEqual(
            Titular.primere(),
            Titular.tomar(pk=pk_titular_principal)
        )
