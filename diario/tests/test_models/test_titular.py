import datetime
from unittest.mock import patch

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
        self.cuenta1 = Cuenta.crear(
            nombre='cuenta1', slug='cta1', titular=self.tit)
        self.cuenta2 = Cuenta.crear(nombre='cuenta2', slug='cta2')
        self.mov1 = Movimiento.crear('Movimiento 1', 120, self.cuenta1)
        self.mov2 = Movimiento.crear('Movimiento 2', 65, None, self.cuenta2)
        self.mov3 = Movimiento.crear(
            'Movimiento 3', 35, self.cuenta1, self.cuenta2, esgratis=True)

    def test_devuelve_movimientos_relacionados_con_cuentas_del_titular(self):
        self.assertEqual(self.tit.movimientos(), [self.mov1, self.mov3])

    def test_no_incluye_movimientos_no_relacionados_con_cuentas_del_titular(self):
        self.assertNotIn(self.mov2, self.tit.movimientos())

    def test_incluye_movimientos_de_cuentas_convertidas_en_acumulativas(self):
        dividir_en_dos_subcuentas(self.cuenta1, saldo=15)
        self.assertIn(self.mov1, self.tit.movimientos())

    def test_incluye_una_sola_vez_traspaso_entre_cuentas_del_mismo_titular(self):
        cuenta3 = Cuenta.crear(nombre='cuenta3', slug='cta3', titular=self.tit)
        self.mov3.cta_salida = cuenta3
        self.mov3.save()
        self.assertEqual(len(self.tit.movimientos()), 2)

    def test_no_incluye_movimientos_de_subcuentas_de_otro_titular_de_cuentas_que_eran_del_titular_originalmente(self):
        tit2 = Titular.crear(titname='juancha', nombre='Juancha Juanchini')
        self.cuenta1.dividir_entre(
            {
                'nombre': 'subcuenta ajena',
                'slug': 'scaj',
                'saldo': 30,
                'titular': tit2
            },
            {'nombre': 'subcuenta propia', 'slug': 'scpr'},
        )
        sc_ajena = CuentaInteractiva.tomar(slug='scaj')
        mov_sc_ajena = Movimiento.crear(
            concepto='Movimiento de subcuenta de otro titular '
                     'de cuenta que era mía',
            importe=10,
            cta_salida=sc_ajena
        )

        self.assertNotIn(mov_sc_ajena, self.tit.movimientos())

    def test_devuelve_movimientos_ordenados_por_fecha(self):
        cuenta3 = Cuenta.crear(nombre='cuenta3', slug='cta3', titular=self.tit)

        self.mov1.fecha = datetime.date(2021, 11, 1)
        self.mov2.fecha = datetime.date(2020, 5, 6)
        self.mov2.cta_salida = cuenta3
        self.mov3.fecha = datetime.date(2021, 11, 22)
        self.mov3.cta_salida = cuenta3
        for mov in (self.mov1, self.mov2, self.mov3):
            mov.save()

        self.assertEqual(
            self.tit.movimientos(), [self.mov2, self.mov1, self.mov3])

    def test_dentro_de_la_fecha_ordena_los_movimientos_por_orden_dia(self):
        mov4 = Movimiento.crear('Movimiento 4', 50, self.cuenta1)
        mov4.orden_dia = 1
        mov4.save()

        self.assertEqual(
            self.tit.movimientos(),
            [self.mov1, mov4, self.mov3]
        )


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


class TestTitularMetodo(TestCase):

    def setUp(self):
        self.titular1 = Titular.crear(titname='tito', nombre='Tito Gomez')
        self.titular2 = Titular.crear(titname='cuco', nombre='Cuco Cuqui')
        self.cuenta1 = Cuenta.crear(
            'Cuenta tito', 'ctito', titular=self.titular1)
        self.cuenta2 = Cuenta.crear(
            'Cuenta cuco', 'ccuco', titular=self.titular2)


class TestTitularMetodoTomarODefault(TestTitularMetodo):

    def test_devuelve_titular_si_existe(self):
        self.assertEqual(
            Titular.tomar_o_default(titname='tito'),
            self.titular1
        )

    def test_devuelve_titular_por_defecto_si_no_encuentra_titular(self):
        self.assertEqual(
            Titular.tomar_o_default(titname='pipo'),
            Titular.tomar(pk=Titular.por_defecto())
        )


class TestTitularMetodoEsDeudorDe(TestTitularMetodo):

    def test_devuelve_false_si_titular_no_esta_entre_deudores_de_otro(self):
        self.assertFalse(self.titular2.es_deudor_de(self.titular1))

    def test_devuelve_true_si_titular_esta_entre_deudores_de_otro(self):
        Movimiento.crear('Prestamo', 10, self.cuenta2, self.cuenta1)
        self.assertTrue(self.titular2.es_deudor_de(self.titular1))


class TestTitularMetodoEsAcreedorDe(TestTitularMetodo):

    def test_devuelve_false_si_titular_no_esta_entre_acreedores_de_otro(self):
        self.assertFalse(self.titular1.es_acreedor_de(self.titular2))

    def test_devuelve_true_si_titular_esta_entre_acreedores_de_otro(self):
        Movimiento.crear('Prestamo', 10, self.cuenta2, self.cuenta1)
        self.assertTrue(self.titular1.es_acreedor_de(self.titular2))


class TestTitularMetodoDeudaCon(TestTitularMetodo):

    def test_devuelve_cuenta_de_deuda_de_titular_con_otro(self):
        Movimiento.crear('Prestamo', 10, self.cuenta2, self.cuenta1)
        self.assertEqual(
            self.titular2.deuda_con(self.titular1),
            Cuenta.tomar(slug='db-cuco-tito')
        )

    def test_si_titular_no_le_debe_a_otro_devuelve_none(self):
        self.assertIsNone(self.titular2.deuda_con(self.titular1))


class TestTitularMetodoDeudaDe(TestTitularMetodo):

    @patch.object(Titular, 'deuda_con', autospec=True)
    def test_devuelve_cuenta_de_deuda_de_otro_con_titular(self, mock_deuda_con):
        Movimiento.crear('Prestamo', 19, self.cuenta2, self.cuenta1)
        self.titular1.deuda_de(self.titular2)
        mock_deuda_con.assert_called_once_with(self.titular2, self.titular1)


class TestTitularMetodoPrestamoA(TestTitularMetodo):

    def test_devuelve_cuenta_de_prestamo_de_titular_a_otro(self):
        Movimiento.crear('Prestamo', 10, self.cuenta2, self.cuenta1)
        self.assertEqual(
            self.titular1.prestamo_a(self.titular2),
            Cuenta.tomar(slug='cr-tito-cuco')
        )

    def test_si_titular_no_le_debe_a_otro_devuelve_none(self):
        self.assertIsNone(self.titular1.prestamo_a(self.titular2))


class TestTitularMetodoPrestamoDe(TestTitularMetodo):

    @patch.object(Titular, 'prestamo_a', autospec=True)
    def test_devuelve_cuenta_de_prestamo_otro_a_titular(self, mock_prestamo_a):
        Movimiento.crear('Prestamo', 19, self.cuenta2, self.cuenta1)
        self.titular2.prestamo_de(self.titular1)
        mock_prestamo_a.assert_called_once_with(self.titular1, self.titular2)


class TestTitularMetodoCancelarDeudaDe(TestTitularMetodo):

    def test_retira_otro_de_deudores_del_titular(self):
        Movimiento.crear('Prestamo', 10, self.cuenta2, self.cuenta1)
        self.titular1.cancelar_deuda_de(self.titular2)
        self.assertNotIn(self.titular2, self.titular1.deudores.all())

    def test_si_otro_no_esta_entre_deudores_del_titular_lanza_excepcion(self):
        Movimiento.crear('Prestamo', 10, self.cuenta2, self.cuenta1)
        tit3 = Titular.crear(nombre='Pipo Pippi', titname='pipo')
        with self.assertRaisesMessage(
            Titular.DoesNotExist,
            'Pipo Pippi no figura entre los deudores de Tito Gomez'
        ):
            self.titular1.cancelar_deuda_de(tit3)
