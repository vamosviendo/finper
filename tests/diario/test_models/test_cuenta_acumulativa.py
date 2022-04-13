from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento, Titular, Saldo
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


class TestSubcuentas(TestCase):
    """ Saldos después de setUp
        self.cta1: 100
        self.cta2: 25
        self.cta3: 75
    """

    def setUp(self):
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )
        self.cta1 = dividir_en_dos_subcuentas(
            self.cta1,
            saldo=25,
            fecha=date(2019, 1, 5)
        )
        self.cta2 = Cuenta.tomar(slug='sc1')
        self.cta3 = Cuenta.tomar(slug='sc2')

    def test_cuenta_acumulativa_debe_tener_subcuentas(self):
        cuenta = Cuenta.crear('cuenta acum', 'ctaa')
        cuenta = cuenta.dividir_y_actualizar(
            ['subc 1', 'suc1', 0], ['subc 2', 'suc2'])
        Cuenta.tomar(slug='suc1').delete()
        Cuenta.tomar(slug='suc2').delete()
        with self.assertRaisesMessage(
            ValidationError,
            'Cuenta acumulativa debe tener subcuentas'
        ):
            cuenta.full_clean()

    def test_cuenta_interactiva_no_puede_tener_subcuentas(self):
        subcuenta = Cuenta.crear("Bolsillos", "ebol")
        with self.assertRaises(ValueError):
            subcuenta.cta_madre = self.cta2  # cta2 interactiva

    def test_no_se_puede_modificar_cuenta_madre_de_subcuenta(self):
        cta4 = Cuenta.crear('cuenta 4', 'c4')
        sc41, sc42 = cta4.dividir_entre(
            ['subcuenta 4.1', 'sc41', 0],
            ['subcuenta 4.2', 'sc42']
        )
        sc41.cta_madre = self.cta1
        with self.assertRaisesMessage(
                ValidationError,
                'No se puede modificar cuenta madre'
        ):
            sc41.full_clean()

    def test_no_se_puede_asignar_cta_madre_a_cta_interactiva_existente(self):
        cta4 = Cuenta.crear("Bolsillo", "ebol", saldo=50)

        cta4.cta_madre = self.cta1

        with self.assertRaises(ValidationError):
            cta4.full_clean()

    def test_no_se_puede_asignar_cta_madre_a_cta_acumulativa_existente(self):
        cta4 = Cuenta.crear("Bolsillos", "ebol", saldo=50)

        cta4 = cta4.dividir_y_actualizar(
            {'nombre': 'Bolsillo campera', 'slug': 'ebca', 'saldo': 30},
            {'nombre': 'Bolsillo pantalón', 'slug': 'ebpa'}
        )

        cta4.cta_madre = self.cta1

        with self.assertRaises(ValidationError):
            cta4.full_clean()

    def test_cuenta_no_puede_ser_subcuenta_de_una_de_sus_subcuentas(self):
        cta4 = Cuenta.crear("Bolsillos", "ebol")
        cta4 = cta4.dividir_y_actualizar(
            {'nombre': 'Bolsillo campera', 'slug': 'ebca', 'saldo': 0},
            {'nombre': 'Bolsillo pantalón', 'slug': 'ebpa'}
        )
        cta4.cta_madre = self.cta1
        cta4.save()
        self.cta1.cta_madre = cta4
        with self.assertRaisesMessage(
                ValidationError,
                'Cuenta madre Bolsillos está entre las subcuentas de Efectivo '
                'o entre las de una de sus subcuentas'
        ):
            self.cta1.full_clean()

    def test_cuenta_no_puede_ser_subcuenta_de_una_subcuenta_de_una_de_sus_subcuentas(self):
        cta4 = Cuenta.crear("Bolsillos", "ebol").dividir_y_actualizar(
            {'nombre': 'Bolsillo campera', 'slug': 'ebca', 'saldo': 0},
            {'nombre': 'Bolsillo pantalón', 'slug': 'ebpa'}
        )

        cta4.cta_madre = self.cta1
        cta4.save()

        cta5 = Cuenta.tomar(slug='ebpa').dividir_y_actualizar(
            {
                'nombre': 'Bolsillo delantero pantalón',
                'slug': 'ebpd',
                'saldo': 0
            },
            {'nombre': 'Bolsillo pantalón trasero', 'slug': 'ebpt'}
        )

        self.cta1.cta_madre = cta5
        with self.assertRaisesMessage(
                ValidationError,
                'Cuenta madre Bolsillo pantalón está entre las subcuentas '
                'de Efectivo o entre las de una de sus subcuentas'
        ):
            self.cta1.full_clean()

    def test_movimiento_en_subcuenta_se_refleja_en_saldo_de_cta_madre(self):

        saldo_cta1 = self.cta1.saldo

        Movimiento.crear(concepto='mov', importe=45, cta_entrada=self.cta2)
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)
        self.assertEqual(
            self.cta1.saldo, saldo_cta1+45,
            'Mov de entrada en subcuenta no se refleja en saldo de cta madre'
        )

    def test_movimiento_en_subcuenta_se_refleja_en_saldo_de_cta_madre_en_fecha_del_movimiento(self):
        saldo = Saldo.tomar(cuenta=self.cta1, fecha=date(2019, 1, 10)).importe

        Movimiento.crear('mov subc', 45, self.cta2, fecha=date(2019, 1, 10))
        self.assertEqual(
            Saldo.tomar(cuenta=self.cta1, fecha=date(2019, 1, 10)).importe,
            saldo+45
        )

    def test_movimiento_en_subcuenta_genera_saldo_en_cuenta_madre_en_fecha_sin_saldo(self):
        self.assertEqual(
            len(Saldo.filtro(cuenta=self.cta1, fecha=date(2019, 1, 10))),
            0
        )
        Movimiento.crear('mov subc', 45, self.cta2, fecha=date(2019, 1, 10))
        self.assertEqual(
            len(Saldo.filtro(cuenta=self.cta1, fecha=date(2019, 1, 10))),
            1
        )

    def test_movimiento_en_subcuenta_suma_importe_a_saldo_existente_en_fecha(self):
        self.assertEqual(
            len(Saldo.filtro(cuenta=self.cta1, fecha=date(2019, 1, 5))),
            1
        )
        saldo = self.cta1.saldo_set.get(fecha=date(2019, 1, 5)).importe
        Movimiento.crear('mov subc', 45, self.cta2, fecha=date(2019, 1, 5))
        self.assertEqual(
            len(Saldo.filtro(cuenta=self.cta1, fecha=date(2019, 1, 5))),
            1
        )
        self.assertEqual(
            self.cta1.saldo_set.get(fecha=date(2019, 1, 5)).importe,
            saldo+45
        )

    def test_movimiento_entre_subcuenta_y_otra_cta_independiente_se_refleja_en_saldo_de_cta_madre(self):
        saldo_cta1 = self.cta1.saldo
        cta4 = Cuenta.crear('Caja de ahorro', 'ca')

        Movimiento.crear(
            concepto='Depósito', importe=20,
            cta_entrada=cta4, cta_salida=self.cta2
        )
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.saldo, saldo_cta1-20)

    def test_movimiento_en_subcuenta_se_refleja_en_saldo_de_cta_abuela(self):

        self.cta3 = self.cta3.dividir_y_actualizar(
            {'nombre': 'Cajita', 'slug': 'eccj', 'saldo': 22},
            {'nombre': 'Sobre', 'slug': 'ecso', 'saldo': 53},
        )
        cta4 = Cuenta.tomar(slug='ecso')

        saldo_cta1 = self.cta1.saldo
        saldo_cta3 = self.cta3.saldo

        Movimiento.crear(concepto='mov2', importe=31, cta_entrada=cta4)
        self.cta3.refresh_from_db()
        self.cta1.refresh_from_db()

        self.assertEqual(
            self.cta3.saldo, saldo_cta3+31,
            'Mov de entada en subcuenta no se refleja en saldo de cta madre'
        )
        self.assertEqual(
            self.cta1.saldo, saldo_cta1+31,
            'Mov de entrada en subcuenta no se refleja en saldo de cta abuela'
        )

        cta5 = Cuenta.tomar(slug='eccj')

        saldo_cta1 = self.cta1.saldo
        saldo_cta3 = self.cta3.saldo

        Movimiento.crear(concepto='mov3', importe=15, cta_salida=cta5)
        self.cta3.refresh_from_db()
        self.cta1.refresh_from_db()

        self.assertEqual(
            self.cta3.saldo, saldo_cta3-15,
            'Mov de salida en subcuenta no se refleja en saldo de cta madre'
        )
        self.assertEqual(
            self.cta1.saldo, saldo_cta1-15,
            'Mov de salida en subcuenta no se refleja en saldo de cta abuela'
        )

    def test_movimiento_entre_subcuentas_no_afecta_saldo_de_cta_madre(self):
        saldo_cta1 = self.cta1.saldo

        Movimiento.crear(
            concepto='mov', importe=45,
            cta_entrada=self.cta2, cta_salida=self.cta3
        )
        self.cta1.refresh_from_db()
        self.assertEqual(
            self.cta1.saldo, saldo_cta1,
            'Mov de entre subcuentas no debe modificar saldo de cuenta madre'
        )

    def test_modificacion_en_movimiento_modifica_saldo_de_cta_madre(self):
        saldo_cta1 = self.cta1.saldo                        # 100
        mov = Movimiento.crear('mov', 45, self.cta2)        # 70
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)       # 145
        self.assertEqual(self.cta1.saldo, saldo_cta1+45)

        mov.importe = 55        # cta1 = 155 - cta2 = 80
        mov.save()
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)
        self.assertEqual(self.cta1.saldo, saldo_cta1+55)

        cta4 = Cuenta.crear('Otro banco', 'ob')
        mov.cta_entrada = cta4
        mov.save()
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)
        self.assertEqual(self.cta1.saldo, saldo_cta1)

        mov.cta_entrada = self.cta2
        mov.cta_salida = self.cta1
        mov.importe = 40
        self.assertEqual(self.cta1.saldo, saldo_cta1)


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
        self.cta_acum.agregar_subcuenta('subcuenta 3', 'sc3')
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
        self.titular = Titular.crear(titname='tito', nombre='Titi Titini')
        self.cta_acum = Cuenta.crear('cta acum', 'ca', titular=self.titular)
        Movimiento.crear('entrada', 200, cta_entrada=self.cta_acum)
        Movimiento.crear('salida', 100, cta_salida=self.cta_acum)
        self.cta_acum = dividir_en_dos_subcuentas(self.cta_acum, saldo=100)

    def test_agregar_subcuenta_crea_nueva_subcuenta(self):
        self.cta_acum.agregar_subcuenta('subc3', 'sc3')
        self.assertEqual(self.cta_acum.subcuentas.count(), 3)

    def test_subcuenta_agregadada_tiene_saldo_cero(self):
        self.cta_acum.agregar_subcuenta('subc3', 'sc3')
        subcuenta = Cuenta.tomar(slug='sc3')
        self.assertEqual(subcuenta.saldo, 0)

    def test_por_defecto_asigna_titular_de_cuenta_madre_a_subcuenta_agregada(self):
        self.cta_acum.agregar_subcuenta('subc3', 'sc3')
        subcuenta = Cuenta.tomar(slug='sc3')
        self.assertEqual(subcuenta.titular, self.titular)

    def test_permite_asignar_titular_distinto_del_de_cuenta_madre(self):
        titular2 = Titular.crear(titname='Pipo', nombre='Pipo Poppo')
        self.cta_acum.agregar_subcuenta('subc3', 'sc3', titular=titular2)
        subcuenta = Cuenta.tomar(slug='sc3')
        self.assertEqual(subcuenta.titular, titular2)


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
