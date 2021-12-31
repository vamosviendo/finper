from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, tag

from diario.models import Cuenta, CuentaInteractiva, Movimiento, Titular

from utils.errors import SaldoNoCeroException, CambioDeTitularException
from utils.helpers_tests import dividir_en_dos_subcuentas


class TestModelCuenta(TestCase):

    def test_guarda_y_recupera_cuentas(self):
        primera_cuenta = Cuenta()
        primera_cuenta.nombre = 'Efectivo'
        primera_cuenta.slug = 'E'
        primera_cuenta.full_clean()
        primera_cuenta.save()

        segunda_cuenta = Cuenta()
        segunda_cuenta.nombre = 'Caja de ahorro'
        segunda_cuenta.slug = 'CA'
        segunda_cuenta.full_clean()
        segunda_cuenta.save()

        cuentas_guardadas = Cuenta.todes()
        self.assertEqual(cuentas_guardadas.count(), 2)

        primera_cuenta_guardada = primera_cuenta.tomar_de_bd()
        segunda_cuenta_guardada = segunda_cuenta.tomar_de_bd()

        self.assertEqual(primera_cuenta_guardada.nombre, 'efectivo')
        self.assertEqual(primera_cuenta_guardada.slug, 'e')
        self.assertEqual(segunda_cuenta_guardada.nombre, 'caja de ahorro')
        self.assertEqual(segunda_cuenta_guardada.slug, 'ca')

    def test_cuenta_creada_tiene_saldo_cero_por_defecto(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E')
        cuenta.save()
        self.assertEqual(cuenta.saldo, 0)

    def test_no_permite_nombres_duplicados(self):
        Cuenta.crear(nombre='Efectivo', slug='E')
        cuenta2 = Cuenta(nombre='Efectivo', slug='EF')
        with self.assertRaises(ValidationError):
            cuenta2.full_clean()

    def test_nombre_se_guarda_en_minusculas(self):
        Cuenta.crear(nombre='Efectivo', slug='Efec')
        cuenta = Cuenta.primere()
        self.assertEqual(cuenta.nombre, 'efectivo')

    def test_no_permite_slugs_duplicados(self):
        Cuenta.crear(nombre='Caja de ahorro', slug='CA')
        with self.assertRaises(ValidationError):
            cuenta2 = Cuenta(nombre='Cuenta de ahorro', slug='CA')
            cuenta2.full_clean()

    def test_no_permite_slug_vacio(self):
        with self.assertRaises(ValidationError):
            cuenta = Cuenta(nombre='Efectivo')
            cuenta.full_clean()

    def test_slug_se_guarda_en_minusculas(self):
        Cuenta.crear(nombre='Efectivo', slug='Efec')
        cuenta = Cuenta.primere()
        self.assertEqual(cuenta.slug, 'efec')

    def test_slug_no_permite_caracteres_no_alfanumericos(self):
        with self.assertRaises(ValidationError):
            Cuenta.crear(nombre='Efectivo', slug='E!ec')

    def test_cuenta_str(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E')
        self.assertEqual(str(cuenta), 'Efectivo')

    def test_no_permite_eliminar_cuentas_con_saldo(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E', saldo=100)
        with self.assertRaises(SaldoNoCeroException):
            cuenta.delete()

    def test_cuentas_se_ordenan_por_nombre(self):
        cuenta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cuenta2 = Cuenta.crear(nombre='Banco', slug='ZZ')
        cuenta3 = Cuenta.crear(nombre='Cuenta Corriente', slug='CC')

        self.assertEqual(list(Cuenta.todes()), [cuenta2, cuenta3, cuenta1])

    def test_guarda_correctamente_valores_con_decimales(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E', saldo= 132.25)
        cuenta.full_clean()
        cuenta.save()
        self.assertEqual(cuenta.saldo, 132.25)


class TestModelCuentaCrear(TestCase):

    def test_crear_crea_cuenta(self):
        Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual(Cuenta.cantidad(), 1)

    @patch('diario.models.cuenta.CuentaInteractiva.crear')
    def test_llama_a_metodo_crear_de_clase_cuentainteractiva(self, mock_crear):
        Cuenta.crear(nombre='Efectivo', slug='e')
        mock_crear.assert_called_once_with(
            nombre='Efectivo', slug='e', cta_madre=None)

    def test_cuenta_creada_es_interactiva(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertIsInstance(cuenta, CuentaInteractiva)

    def test_crear_devuelve_cuenta_creada(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual((cuenta.nombre, cuenta.slug), ('efectivo', 'e'))

    def test_crear_no_permite_nombre_vacio(self):
        with self.assertRaises(ValidationError):
            Cuenta.crear(nombre=None, slug='E')

    def test_crear_no_permite_slug_vacio(self):
        with self.assertRaises(ValidationError):
            Cuenta.crear(nombre='Efectivo', slug=None)


class TestModelCuentaTitular(TestCase):

    def test_cuenta_no_puede_cambiar_de_titular(self):
        titular1 = Titular.crear(titname='tito', nombre='Tito Titi')
        titular2 = Titular.crear(titname='pipo', nombre='Pipo Pippi')
        self.cuenta = Cuenta.crear('cuenta propia', 'cp', titular=titular1)

        self.cuenta.titular = titular2

        with self.assertRaises(CambioDeTitularException):
            self.cuenta.full_clean()


class TestModelCuentaPropiedadSaldo(TestCase):
    """ Saldos después de setUp
        self.cta1: 100
    """

    def setUp(self):
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )

    def test_devuelve_el_saldo_de_la_cuenta(self):
        self.assertEqual(self.cta1.saldo, self.cta1._saldo)

    def test_asigna_saldo_a_cuenta(self):
        self.cta1.saldo = 300
        self.assertEqual(self.cta1._saldo, 300)

    def test_redondea_saldo(self):
        self.cta1.saldo = 354.452
        self.assertEqual(self.cta1._saldo, 354.45)


class TestModelCuentaMetodos(TestCase):
    """ Testea: Cuenta.movs_directos()
                Cuenta.movs()
                Cuenta.cantidad_movs()
                Cuenta.total_movs()
                Cuenta.total_subcuentas()
                Cuenta.fecha_ultimo_mov_directo()
                Cuenta.saldo_ok()
                Cuenta.corregir_saldo()
                Cuenta.agregar_movimiento_correctivo()
                ...
        Saldos después del setUp:
        self.cta1.saldo == 100-70+80 = 110
        self.cta2.saldo == 70+50 = 120
    """

    def setUp(self):
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        self.cta2 = Cuenta.crear('Banco', 'B')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )
        Movimiento.crear(
            concepto='mov2', importe=70,
            cta_entrada= self.cta2, cta_salida=self.cta1,
            fecha=date(2021, 8, 10)
        )
        Movimiento.crear(
            concepto='mov3', importe=80,
            cta_entrada=self.cta1, fecha=date(2021, 8, 5)
        )
        Movimiento.crear(
            concepto='mov4', importe=50,
            cta_entrada=self.cta2, fecha=date(2021, 8, 1)
        )


@tag('metodos')
class TestModelCuentaMetodosMovsDirectos(TestModelCuentaMetodos):

    def test_devuelve_todos_los_movimientos_de_una_cuenta(self):
        movs_cta1 = [
            Movimiento.tomar(concepto='00000'),
            Movimiento.tomar(concepto='mov2'),
            Movimiento.tomar(concepto='mov3'),
        ]
        movs_directos = self.cta1.movs_directos()

        self.assertEqual(len(movs_directos), 3)
        for mov in movs_cta1:
            self.assertIn(mov, movs_directos)

    def test_no_incluye_los_movimientos_de_subcuentas(self):
        subcuentas = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 30, },
            {'nombre': 'Cajoncito', 'slug': 'ec', }
        )
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)
        mov_subcuenta = Movimiento.crear(
            concepto='movsubc', importe=10, cta_salida=subcuentas[0])

        self.assertNotIn(mov_subcuenta, self.cta1.movs_directos())


@tag('metodos')
class TestModelCuentaMetodosMovs(TestModelCuentaMetodos):

    def test_devuelve_todos_los_movimientos_de_una_cuenta(self):
        movs_cta1 = [
            Movimiento.tomar(concepto='00000'),
            Movimiento.tomar(concepto='mov2'),
            Movimiento.tomar(concepto='mov3'),
        ]
        for mov in movs_cta1:
            self.assertIn(mov, self.cta1.movs())

    def test_incluye_movimientos_de_subcuentas(self):
        subcuentas = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 30, },
            {'nombre': 'Cajoncito', 'slug': 'ec', }
        )
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)
        mov_subcuenta = Movimiento.crear(
            concepto='movsubc', importe=10, cta_salida=subcuentas[0])

        self.assertIn(mov_subcuenta, self.cta1.movs())

        subsubctas = Cuenta.tomar(slug='eb').dividir_entre(
            {'nombre': 'Primera billetera', 'slug': 'eb1', 'saldo': 15},
            {'nombre': 'Segunda billetera', 'slug': 'eb2', },
        )
        mov_subsubc = Movimiento.crear(
            concepto='movsubsub', importe=5, cta_salida=subsubctas[1])

        self.assertIn(mov_subsubc, self.cta1.movs())

    def test_devuelve_movimientos_ordenados_por_fecha(self):
        m1 = Movimiento.tomar(concepto='00000')
        m2 = Movimiento.tomar(concepto='mov2')
        m3 = Movimiento.tomar(concepto='mov3')

        self.assertEqual(
            list(self.cta1.movs()),
            [m1, m3, m2]
        )


@tag('metodos')
class TestModelCuentaMetodosCantidadMovs(TestModelCuentaMetodos):

    def test_devuelve_cantidad_de_entradas_mas_cantidad_de_salidas(self):
        self.assertEqual(self.cta1.cantidad_movs(), 3)


@tag('metodos')
class TestModelCuentaMetodosTotalMovs(TestModelCuentaMetodos):

    def test_devuelve_suma_de_importes_de_entradas_menos_suma_de_importes_de_salidas(self):
        self.assertEqual(self.cta1.total_movs(), 110)

    def test_funciona_correctamente_con_decimales(self):
        Movimiento.crear(
            'Movimiento con decimales', cta_salida=self.cta1, importe=50.32)

        self.assertEqual(self.cta1.total_movs(), round(110-50.32, 2))


@tag('metodos')
class TestModelCuentaMetodosFechaUltimoMovDirecto(TestModelCuentaMetodos):

    def test_devuelve_fecha_ultimo_movimiento(self):
        self.assertEqual(
            self.cta1.fecha_ultimo_mov_directo(),
            date(2021, 8, 10)
        )

    def test__devuelve_none_si_no_hay_movimientos(self):
        Movimiento.todes().delete()
        self.assertIsNone(self.cta1.fecha_ultimo_mov_directo())

    def test_en_cta_acumulativa_devuelve_ultimo_mov_directo(self):

        subcuenta1 = self.cta1.dividir_entre(
            ['subcuenta1', 'sc1', 100],
            ['subcuenta2', 'sc2'],
            fecha=date(2021, 8, 11)
        )[0]
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)

        Movimiento.crear(
            'cuarto movimiento', 100, subcuenta1, fecha=date(2021, 8, 20))

        self.assertEqual(
            self.cta1.fecha_ultimo_mov_directo(),
            date(2021, 8, 11)
        )


@tag('metodos')
class TestModelCuentaMetodosTotalSubcuentas(TestModelCuentaMetodos):

    def test_devuelve_suma_saldos_subcuentas(self):
        self.cta1 = self.cta1.dividir_y_actualizar(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 15},
            {'nombre': 'Cajón', 'slug': 'ec', 'saldo': 65},
            {'nombre': 'Cajita', 'slug': 'eca', }
        )
        cta2 = Cuenta.tomar(slug='eb')
        Movimiento.crear('Movimiento', 5, cta_salida=cta2)
        self.assertEqual(self.cta1.total_subcuentas(), 110-5)

        Movimiento.crear('Movimiento con decimales', 4.45, cta_salida=cta2)
        self.assertEqual(
            self.cta1.total_subcuentas(), round(105-4.45, 2),
            'No funciona correctamente con decimales'
        )


@tag('metodos')
class TestModelCuentaMetodosCorregirSaldo(TestModelCuentaMetodos):

    def test_no_agrega_movimientos(self):
        self.cta1.saldo = 345
        self.cta1.save()
        entradas = self.cta1.entradas.count()
        salidas = self.cta1.salidas.count()
        self.cta1.corregir_saldo()
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.entradas.count(), entradas)
        self.assertEqual(self.cta1.salidas.count(), salidas)


@tag('metodos')
class TestModelCuentaMetodosAgregarMovCorrectivo(TestModelCuentaMetodos):

    def test_agrega_un_movimiento(self):
        self.cta1.saldo = 880
        self.cta1.save()
        cant_movs = self.cta1.cantidad_movs()
        self.cta1.agregar_mov_correctivo()
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.cantidad_movs(), cant_movs+1)

    def test_devuelve_un_movimiento(self):
        self.cta1.saldo = 880
        self.cta1.save()
        self.assertIsInstance(self.cta1.agregar_mov_correctivo(), Movimiento)

    def test_no_acepta_ctas_acumulativas(self):
        self.cta1 = dividir_en_dos_subcuentas(self.cta1)
        self.cta1.saldo = 945
        self.cta1.save()
        with self.assertRaises(AttributeError):
            self.cta1.agregar_mov_correctivo()

    def test_importe_del_mov_correctivo_coincide_con_diferencia_con_saldo(self):
        self.cta1.saldo = 880
        self.cta1.save()
        mov = self.cta1.agregar_mov_correctivo()
        self.assertEqual(mov.importe, 770)

    def test_importe_es_siempre_positivo(self):
        self.cta2.saldo = 70
        self.cta2.save()
        mov = self.cta2.agregar_mov_correctivo()
        self.assertGreater(mov.importe, 0)

    def test_cuenta_es_de_entrada_o_salida_segun_signo_de_la_diferencia(self):
        self.cta1.saldo = 880
        self.cta1.save()
        mov1 = self.cta1.agregar_mov_correctivo()
        self.assertEqual(mov1.cta_entrada, self.cta1)

        self.cta2.saldo = 70
        self.cta2.save()
        mov2 = self.cta2.agregar_mov_correctivo()
        self.assertEqual(mov2.cta_salida, self.cta2)

    def test_no_modifica_saldo(self):
        self.cta1.saldo = 880
        self.cta1.save()
        mov1 = self.cta1.agregar_mov_correctivo()
        self.assertEqual(self.cta1.saldo, 880)

    def test_no_agrega_movimiento_si_saldo_es_correcto(self):
        cant_movs = self.cta1.cantidad_movs()
        mov = self.cta1.agregar_mov_correctivo()
        self.assertEqual(self.cta1.cantidad_movs(), cant_movs)
        self.assertIsNone(mov)


@tag('metodos')
class TestModelCuentaMetodosHermanas(TestModelCuentaMetodos):

    def test_devuelve_hijas_de_la_misma_madre(self):
        subc1, subc2, subc3 = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 30, },
            {'nombre': 'Cajoncito', 'slug': 'ec', 'saldo': 1},
            {'nombre': 'Bolsillo', 'slug': 'ebo'}
        )
        for subc in [subc2, subc3]:
            self.assertIn(subc, subc1.hermanas())

    def test_cuenta_no_se_incluye_a_si_misma_entre_sus_hermanas(self):
        subc1, subc2, subc3 = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 30, },
            {'nombre': 'Cajoncito', 'slug': 'ec', 'saldo': 1},
            {'nombre': 'Bolsillo', 'slug': 'ebo'}
        )
        self.assertNotIn(subc1, subc1.hermanas())

    def test_devuelve_lista_vacia_si_no_tiene_hermanas(self):
        subc1, subc2, subc3 = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 110, },
            {'nombre': 'Cajoncito', 'slug': 'ec', 'saldo': 0},
            {'nombre': 'Bolsillo', 'slug': 'ebo', 'saldo': 0}
        )
        subc2.delete()
        subc3.delete()
        self.assertEqual(list(subc1.hermanas()), [])

    def test_devuelve_none_si_cuenta_no_tiene_madre(self):
        self.assertIsNone(self.cta2.hermanas())


class TestCuentaPolymorphic(TestCase):

    def test_tomar_devuelve_cuenta_de_la_clase_correcta(self):
        cta = Cuenta.crear('Efectivo', 'e')
        cta_nueva = Cuenta.tomar(pk=cta.pk)
        self.assertIsInstance(cta_nueva, CuentaInteractiva)


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
        self.cta1 = dividir_en_dos_subcuentas(self.cta1, saldo=25)
        self.cta2 = Cuenta.tomar(slug='sc1')
        self.cta3 = Cuenta.tomar(slug='sc2')

    def test_cuenta_caja_debe_tener_subcuentas(self):
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

    def test_se_puede_asignar_cta_interactiva_a_cta_caja(self):
        cta4 = Cuenta.crear("Bolsillo", "ebol")
        cta4.cta_madre = self.cta1
        cta4.save()
        self.assertEqual(self.cta1.subcuentas.count(), 3)

    def test_se_puede_asignar_cta_caja_a_otra_cta_caja(self):
        cta4 = Cuenta.crear("Bolsillos", "ebol")
        cta4.dividir_entre(
            {'nombre': 'Bolsillo campera', 'slug': 'ebca', 'saldo': 0},
            {'nombre': 'Bolsillo pantalón', 'slug': 'ebpa'}
        )
        cta4.cta_madre = self.cta1
        cta4.save()
        self.assertEqual(self.cta1.subcuentas.count(), 3)

    def test_si_se_asigna_cta_interactiva_con_saldo_a_cta_caja_se_suma_el_saldo(self):
        saldo_cta1 = self.cta1.saldo    # 100
        cta4 = Cuenta.crear("Bolsillo", "ebol", saldo=50)

        cta4.cta_madre = self.cta1
        cta4.save()

        self.assertEqual(cta4.saldo, 50)
        self.assertEqual(self.cta1.saldo, saldo_cta1 + 50)

    def test_si_se_asigna_cta_caja_con_saldo_a_cta_caja_se_suma_el_saldo(self):
        saldo_cta1 = self.cta1.saldo    # 100
        cta4 = Cuenta.crear("Bolsillos", "ebol", saldo=50)

        cta4 = cta4.dividir_y_actualizar(
            {'nombre': 'Bolsillo campera', 'slug': 'ebca', 'saldo': 30},
            {'nombre': 'Bolsillo pantalón', 'slug': 'ebpa'}
        )

        cta4.cta_madre = self.cta1
        cta4.save()

        self.assertEqual(cta4.saldo, 50)
        self.assertEqual(self.cta1.saldo, saldo_cta1 + 50)

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


class TestMetodosSubcuentas(TestCase):
    """ Testea: Cuenta.tiene_madre()
                Cuenta.arbol_de_subcuentas()
    """
    def setUp(self):
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )

    # Cuenta.tiene_madre()
    def test_tiene_madre_devuelve_true_si_tiene_cta_madre(self):
        self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 40},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 60},
        )

        cta2 = Cuenta.tomar(slug='ebil')
        cta3 = Cuenta.tomar(slug='ecaj')

        self.assertTrue(cta2.tiene_madre())
        self.assertFalse(self.cta1.tiene_madre())

    # Cuenta.arbol_de_subcuentas()
    def test_arbol_de_subcuentas_devuelve_set_con_todas_las_cuentas_dependientes(self):
        lista_subcuentas = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 0},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', },
        )
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)

        lista_subcuentas += lista_subcuentas[0].dividir_entre(
            {
                'nombre': 'Billetera división delantera',
                'slug': 'ebdd',
                'saldo': 0,
            },
            {'nombre': 'Billetera división trasera', 'slug': 'ebdt', },
        )
        lista_subcuentas[0] = Cuenta.tomar(slug=lista_subcuentas[0].slug)

        lista_subcuentas += lista_subcuentas[2].dividir_entre(
            {
                'nombre': 'Billetera división delantera izquierda',
                'slug': 'ebdi',
                'saldo': 0,
            },
            {
                'nombre': 'Billetera división delantera derecha',
                'slug': 'ebdr',
            },
        )
        lista_subcuentas[2] = Cuenta.tomar(slug=lista_subcuentas[2].slug)

        lista_subcuentas += lista_subcuentas[1].dividir_entre(
            {
                'nombre': 'Cajita verde',
                'slug': 'eccv',
                'saldo': 0,
            },
            {'nombre': 'Sobre', 'slug': 'ecs', },
        )
        lista_subcuentas[1] = Cuenta.tomar(slug=lista_subcuentas[1].slug)

        self.assertEqual(
            self.cta1.arbol_de_subcuentas(), set(lista_subcuentas))
