from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, tag

from diario.models import Cuenta, CuentaInteractiva, Movimiento, Saldo, Titular

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

    def test_guarda_fecha_de_creacion(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E', fecha_creacion=date(2010, 11, 12))
        cuenta.full_clean()
        cuenta.save()

        self.assertEqual(cuenta.fecha_creacion, date(2010, 11, 12))

    def test_guarda_fecha_actual_por_defecto(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E')
        cuenta.full_clean()
        cuenta.save()

        self.assertEqual(cuenta.fecha_creacion, date.today())

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

    def test_devuelve_el_ultimo_saldo_historico_de_la_cuenta(self):
        mov = Movimiento.crear(
            concepto='00001',
            importe=40,
            cta_salida=self.cta1,
            fecha=(date(2019, 1, 2))
        )
        self.assertEqual(
            self.cta1.saldo,
            Saldo.objects.get(cuenta=self.cta1, movimiento=mov).importe
        )

    def test_si_no_encuentra_saldos_en_la_cuenta_devuelve_cero(self):
        cta2 = Cuenta.crear('cta2', 'c2', fecha_creacion=(date(2019, 1, 1)))
        self.assertEqual(
            cta2.saldo,
            0.0
        )

    def test_devuelve_el_saldo_de_la_cuenta(self):
        self.assertEqual(self.cta1.saldo, self.cta1._saldo)

    def test_asigna_saldo_a_cuenta(self):
        self.cta1.saldo = 300
        self.assertEqual(self.cta1._saldo, 300)

    def test_redondea_saldo(self):
        self.cta1.saldo = 354.452
        self.assertEqual(self.cta1._saldo, 354.45)


class TestModelCuentaPropiedadUltimoHistorico(TestCase):

    def setUp(self):
        self.cta1 = Cuenta.crear(
            'cuenta 1', 'c1',
            fecha_creacion=date(2019, 1, 1)
        )

    def test_si_cuenta_no_tiene_saldos_historicos_devuelve_cero(self):
        self.assertEqual(
            self.cta1.ultimo_historico,
            0
        )

    def test_devuelve_importe_del_ultimo_saldo_historico_de_la_cuenta(self):
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )
        Movimiento.crear(
            concepto='00001',
            importe=70,
            cta_salida=self.cta1,
            fecha=date(2019, 2, 3)
        )
        self.assertEqual(
            self.cta1.ultimo_historico,
            # self.cta1.saldo_set.last().importe
            30
        )


class TestModelCuentaPropiedadEsCuentaCredito(TestCase):

    def setUp(self):
        super().setUp()
        self.titular1 = Titular.crear(nombre='Titular 1', titname='tit1')
        self.titular2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta1 = Cuenta.crear(
            'Cuenta titular 1', 'ct1', titular=self.titular1)
        self.cuenta2 = Cuenta.crear(
            'Cuenta titular 2', 'ct2', titular=self.titular2)
        self.mov = Movimiento.crear(
            'tit2 a tit1', 100, self.cuenta1, self.cuenta2)

    def test_devuelve_false_si_cuenta_no_es_cuenta_credito(self):
        self.assertFalse(self.cuenta1.es_cuenta_credito)

    def test_devuelve_true_si_cuenta_es_cuenta_credito(self):
        cc2, cc1 = self.mov.recuperar_cuentas_credito()
        self.assertTrue(cc2.es_cuenta_credito)

    def test_devuelve_false_si_cuenta_no_es_interactiva(self):
        self.cuenta1 = dividir_en_dos_subcuentas(self.cuenta1)
        self.assertFalse(self.cuenta1.es_cuenta_credito)


class TestModelCuentaMetodos(TestCase):
    """ Saldos después del setUp:
        self.cta1.saldo == 100-70+80 = 110
        self.cta2.saldo == 70+50 = 120
    """

    def setUp(self):
        self.cta1 = Cuenta.crear(
            'Efectivo', 'E', fecha_creacion=date(2019, 1, 1))
        self.cta2 = Cuenta.crear('Banco', 'B', fecha_creacion=date(2019, 1, 1))
        self.mov1 = Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )
        self.mov2 = Movimiento.crear(
            concepto='mov2', importe=70,
            cta_entrada= self.cta2, cta_salida=self.cta1,
            fecha=date(2021, 8, 10)
        )
        self.mov3 = Movimiento.crear(
            concepto='mov3', importe=80,
            cta_entrada=self.cta1, fecha=date(2021, 8, 5)
        )
        self.mov4 = Movimiento.crear(
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
class TestModelCuentaMetodosMovsDirectosEnFecha(TestModelCuentaMetodos):

    def test_con_cuenta_interactiva_devuelve_movs_de_cuenta_en_fecha(self):
        mov5 = Movimiento.crear('otro mov', 100, self.cta1, fecha=self.mov1.fecha)
        self.assertEqual(
            list(self.cta1.movs_directos_en_fecha(self.mov1.fecha)),
            [self.mov1, mov5]
        )

    def test_con_cuenta_acumulativa_devuelve_solo_movs_directos_de_cuenta_en_fecha(self):
        fecha = date(2021, 8, 10)
        self.cta1 = dividir_en_dos_subcuentas(self.cta1, fecha=fecha)
        sc1 = Cuenta.tomar(slug='sc1')
        mov = Movimiento.crear('mov subcuenta', 100, sc1, fecha=fecha)
        self.assertNotIn(mov, self.cta1.movs_directos_en_fecha(fecha))


@tag('metodos')
class TestModelCuentaMetodosMovsEnFecha(TestModelCuentaMetodos):

    def test_con_cuenta_interactiva_devuelve_lo_mismo_que_movs_directos_en_fecha(self):
        mov5 = Movimiento.crear('otro mov', 100, self.cta1, fecha=self.mov1.fecha)
        self.assertEqual(
            list(self.cta1.movs_en_fecha(self.mov1.fecha)),
            list(self.cta1.movs_directos_en_fecha(self.mov1.fecha))
        )

    def test_con_cuenta_acumulativa_devuelve_movs_propios_y_de_subcuentas_en_fecha(self):
        fecha = date(2021, 8, 10)
        self.cta1 = dividir_en_dos_subcuentas(self.cta1, fecha=fecha)
        sc1 = Cuenta.tomar(slug='sc1')
        mov = Movimiento.crear('mov subcuenta', 100, sc1, fecha=fecha)
        self.assertIn(mov, self.cta1.movs_en_fecha(fecha))


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
        sc11, sc12 = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 30, },
            {'nombre': 'Cajoncito', 'slug': 'ec', }
        )
        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)
        mov_subcuenta = Movimiento.crear(
            concepto='movsubc', importe=10, cta_salida=sc11)

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


@tag('metodos')
class TestModelCuentaMetodosAncestros(TestModelCuentaMetodos):

    def test_devuelve_lista_de_todas_las_cuentas_ancestro(self):
        subc1, subc2 = self.cta1.dividir_entre(
            ['subcuenta 1', 'sc1', 0],
            ['subcuenta 2', 'sc2']
        )
        subsubc1, subsubc2 = subc1.dividir_entre(
            ['subsubcuenta 1', 'ssc1', 0],
            ['subsubcuenta 2', 'ssc2']
        )
        subsubsubc1, subsubsubc2 = subsubc1.dividir_entre(
            ['subsubsubcuenta 1', 'sssc1', 0],
            ['subsubsubcuenta 2', 'sssc2']
        )
        subsubc1 = Cuenta.tomar(slug=subsubc1.slug)
        subc1 = Cuenta.tomar(slug=subc1.slug)
        cta1 = Cuenta.tomar(slug=self.cta1.slug)

        self.assertEqual(
            subsubsubc1.ancestros(),
            [subsubc1, subc1, cta1]
        )


@patch('diario.models.cuenta.Saldo.tomar', autospec=True)
@patch('diario.models.cuenta.Movimiento.filtro')
class TestModelCuentaMetodosSaldoHistorico(TestCase):

    def setUp(self):
        self.cta1 = Cuenta.crear(
            'cuenta1', 'c1', fecha_creacion=date(2019, 1, 1))
        self.cta2 = Cuenta.crear(
            'cuenta2', 'c2', fecha_creacion=date(2019, 1, 1))
        self.mov1 = Movimiento.crear(
            'Movimiento cero', 100, self.cta1, fecha=date(2019, 1, 1))

    def test_recupera_saldo_al_momento_del_movimiento(self, mock_filtro, mock_tomar):
        self.cta1.saldo_historico(self.mov1)
        mock_tomar.assert_called_once_with(cuenta=self.cta1, movimiento=self.mov1)

    def test_si_no_encuentra_saldo_de_cuenta_en_fecha_de_mov_devuelve_0(self, mock_filtro, mock_tomar):
        mock_tomar.side_effect = Saldo.DoesNotExist
        cuenta = Cuenta.crear('cuenta sin movimientos', 'csm')
        self.assertEqual(cuenta.saldo_historico(self.mov1), 0)


class TestModelCuentaMetodosTomarDeBd(TestCase):

    def test_actualiza_cambios_en_cuentas_interactivas(self):
        cuenta = CuentaInteractiva.crear('cuenta', 'c')

        variable = Cuenta.tomar(slug='c')
        cuenta.nombre = 'kuenta'
        cuenta.save()

        variable = variable.tomar_de_bd()

        self.assertEqual(variable.nombre, 'kuenta')

    def test_actualiza_cambios_en_cuentas_acumulativas(self):
        cuenta = Cuenta.crear('cuenta', 'c')
        cuenta = cuenta._convertirse_en_acumulativa()
        variable = Cuenta.tomar(slug='c')
        cuenta.nombre = 'kuenta'
        cuenta.save()

        variable = variable.tomar_de_bd()

        self.assertEqual(variable.nombre, 'kuenta')


class TestCuentaPolymorphic(TestCase):

    def test_tomar_devuelve_cuenta_de_la_clase_correcta(self):
        cta = Cuenta.crear('Efectivo', 'e')
        cta_nueva = Cuenta.tomar(pk=cta.pk)
        self.assertIsInstance(cta_nueva, CuentaInteractiva)


class TestMetodosSubcuentas(TestCase):
    """ Testea: Cuenta.tiene_madre()
                Cuenta.arbol_de_subcuentas()
    """
    def setUp(self):
        self.cta1 = Cuenta.crear(
            'Efectivo', 'E', fecha_creacion=date(2019, 1, 1))
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

        lista_subcuentas[1] = Cuenta.tomar(slug=lista_subcuentas[1].slug)
        lista_subcuentas += lista_subcuentas[1].dividir_entre(
            {
                'nombre': 'Cajita verde',
                'slug': 'eccv',
                'saldo': 0,
            },
            {'nombre': 'Sobre', 'slug': 'ecs', },
        )
        lista_subcuentas[1] = Cuenta.tomar(slug=lista_subcuentas[1].slug)

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

        self.assertEqual(
            self.cta1.arbol_de_subcuentas(), set(lista_subcuentas))
