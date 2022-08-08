from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento, Titular, Saldo
from utils import errors
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
        self.cta1 = Cuenta.crear(
            'Efectivo', 'E',
            fecha_creacion=date(2019, 1, 1)
        )
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
                errors.CAMBIO_CUENTA_MADRE
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

    def test_movimiento_en_subcuenta_se_refleja_en_saldo_de_cta_madre(self):

        saldo_cta1 = self.cta1.saldo

        Movimiento.crear(concepto='mov', importe=45, cta_entrada=self.cta2)

        self.assertEqual(
            self.cta1.saldo, saldo_cta1+45,
            'Mov de entrada en subcuenta no se refleja en saldo de cta madre'
        )

    def test_movimiento_en_subcuenta_se_refleja_en_saldo_de_cta_madre_en_nuevo_movimiento(self):
        mov = Movimiento.tomar(cta_entrada=self.cta3)
        saldo = Saldo.tomar(cuenta=self.cta1, movimiento=mov).importe

        mov2 = Movimiento.crear('mov subc', 45, self.cta2, fecha=date(2019, 1, 5))

        self.assertEqual(
            Saldo.tomar(cuenta=self.cta1, movimiento=mov2).importe,
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
        self.assertEqual(self.cta1.saldo, saldo_cta1+45)

        mov.importe = 55        # cta1 = 155 - cta2 = 80
        mov.save()
        self.assertEqual(self.cta1.saldo, saldo_cta1+55)

        cta4 = Cuenta.crear('Otro banco', 'ob')
        mov.cta_entrada = cta4
        mov.save()
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


class TestSaldo(TestCase):

    def setUp(self):
        self.fecha = date(2010, 1, 2)
        cta_acum = Cuenta.crear(
            'cta acumulativa', 'ca', fecha_creacion=self.fecha)
        self.sc1, self.sc2 = cta_acum.dividir_entre(
            ['subcuenta 1', 'sc1', 0],
            ['subcuenta 2', 'sc2'],
            fecha=self.fecha
        )
        self.cta_acum = cta_acum.tomar_del_slug()
        Movimiento.crear('saldo sc1', 100, self.sc1, fecha=self.fecha)
        Movimiento.crear('saldo sc2', 70, None, self.sc2, fecha=self.fecha)

    def test_devuelve_suma_de_saldos_de_subcuentas_interactivas(self):
        self.assertEqual(
            self.cta_acum.saldo,
            100-70
        )

    def test_devuelve_suma_de_saldos_incluyendo_subcuentas_acumulativas(self):
        sc11, sc12 = self.sc1.dividir_entre(
            ['subsubcuenta 1.1', 'sc11', 30],
            ['subsubcuenta 1.2', 'sc12'],
            fecha=self.fecha
        )
        Movimiento.crear('saldo sc11', 60, sc11, fecha=self.fecha)
        self.sc1 = self.sc1.tomar_del_slug()

        self.assertEqual(
            self.sc1.saldo,
            90+70
        )

        self.assertEqual(
            self.cta_acum.saldo,
            160-70
        )


class TestSave(TestCase):

    def setUp(self):
        self.cta1 = Cuenta.crear(
            'Efectivo', 'E',
            fecha_creacion=date(2011, 1, 1)
        )
        self.mov1 = Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 2)
        )
        self.mov2 = Movimiento.crear(
            concepto='00000', importe=150, cta_entrada=self.cta1,
            fecha=date(2019, 1, 4)
        )
        self.subcuentas = [
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200},
        ]

    def test_permite_cambiar_fecha_de_conversion_de_cuenta_por_fecha_posterior(self):
        self.cta1 = self.cta1.dividir_y_actualizar(*self.subcuentas, fecha=date(2020, 10, 5))
        self.cta1.fecha_conversion = date(2021, 10, 6)
        self.cta1.full_clean()
        self.cta1.save()

        self.assertEqual(self.cta1.fecha_conversion, date(2021, 10, 6))

    def test_si_se_modifica_fecha_de_conversion_de_cuenta_se_modifica_fecha_de_movimientos_de_traspaso_de_saldo(
            self):
        sc1, sc2 = self.cta1.dividir_entre(*self.subcuentas, fecha=date(2020, 10, 5))

        self.cta1 = self.cta1.tomar_del_slug()
        self.cta1.fecha_conversion = date(2021, 1, 6)
        self.cta1.full_clean()
        self.cta1.save()

        mov1 = Movimiento.tomar(cta_entrada=sc1)
        mov2 = Movimiento.tomar(cta_entrada=sc2)

        self.assertEqual(mov1.fecha, date(2021, 1, 6))
        self.assertEqual(mov2.fecha, date(2021, 1, 6))

    def test_funciona_con_cuenta_convertida_como_cta_entrada_de_movimiento_de_traspaso(self):
        cuenta = Cuenta.crear('cuenta', 'c', fecha_creacion=date(2021, 1, 1))
        sc1, sc2 = cuenta.dividir_entre(
            ['subc1', 'sc1', 100],
            ['subc2', 'sc2'],
            fecha=date(2020, 10, 5)
        )
        cuenta = cuenta.tomar_del_slug()
        cuenta.fecha_conversion = date(2021, 1, 6)
        cuenta.full_clean()
        cuenta.save()
        mov1 = Movimiento.tomar(cta_entrada=sc1)
        mov2 = Movimiento.tomar(cta_salida=sc2)

        self.assertEqual(mov1.fecha, date(2021, 1, 6))
        self.assertEqual(mov2.fecha, date(2021, 1, 6))

    def test_no_permite_cambiar_fecha_de_conversion_por_una_anterior_a_la_de_cualquier_movimiento_de_la_cuenta(self):
        self.cta1 = self.cta1.dividir_y_actualizar(*self.subcuentas, fecha=date(2020, 10, 5))
        self.cta1.fecha_conversion = date(2019, 1, 3)

        with self.assertRaisesMessage(
            ValidationError,
            'La fecha de conversión no puede ser anterior a la del último '
            'movimiento de la cuenta (2019-01-04)'
        ):
            self.cta1.full_clean()


class TestMovsConversion(TestCase):

    def setUp(self):
        self.cta1 = Cuenta.crear(
            'Efectivo', 'E',
            fecha_creacion=date(2011, 1, 1)
        )
        self.subcuentas = [
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj'},
        ]

    def test_devuelve_movimientos_de_traspaso_de_saldo_generados_al_momento_de_la_conversion_en_acumulativa(self):
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )
        sc1, sc2 = self.cta1.dividir_entre(*self.subcuentas, fecha=date(2020, 10, 5))
        self.cta1 = self.cta1.tomar_del_slug()

        mov1 = Movimiento.tomar(cta_entrada=sc1)
        mov2 = Movimiento.tomar(cta_entrada=sc2)

        self.assertQuerysetEqual(self.cta1.movs_conversion(), [mov1, mov2])

    def test_si_no_se_generaron_movimientos_al_momento_de_la_conversion_en_acumulativa_devuelve_lista_vacia(self):
        self.subcuentas[0]['saldo'] = 0
        self.cta1 = self.cta1.dividir_y_actualizar(*self.subcuentas, fecha=date(2020, 10, 5))

        self.assertQuerysetEqual(self.cta1.movs_conversion(), [])


class TestMovsNoConversion(TestCase):

    def setUp(self):
        self.cta1 = Cuenta.crear(
            'Efectivo', 'E',
            fecha_creacion=date(2011, 1, 1)
        )
        self.mov1 = Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 2)
        )
        self.mov2 = Movimiento.crear(
            concepto='00000', importe=150, cta_entrada=self.cta1,
            fecha=date(2019, 1, 4)
        )
        self.subcuentas = [
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200},
        ]

    def test_devuelve_todos_los_movimientos_de_la_cuenta_excepto_los_de_conversion(self):
        self.cta1 = self.cta1.dividir_y_actualizar(*self.subcuentas, fecha=date(2020, 10, 5))

        self.assertQuerysetEqual(self.cta1.movs_no_conversion(), [self.mov1, self.mov2])
