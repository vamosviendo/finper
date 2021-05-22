from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento

from utils.errors import SaldoNoCeroException, ErrorOpciones


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

        primera_cuenta_guardada = Cuenta.tomar(pk=primera_cuenta.pk)
        segunda_cuenta_guardada = Cuenta.tomar(pk=segunda_cuenta.pk)

        self.assertEqual(primera_cuenta_guardada.nombre, 'Efectivo')
        self.assertEqual(primera_cuenta_guardada.slug, 'e')
        self.assertEqual(segunda_cuenta_guardada.nombre, 'Caja de ahorro')
        self.assertEqual(segunda_cuenta_guardada.slug, 'ca')

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
        self.assertEqual(cuenta.slug, 'efec')

    def test_slug_no_permite_caracteres_no_alfanumericos(self):
        with self.assertRaises(ValidationError):
            Cuenta.crear(nombre='Efectivo', slug='E!ec')

    def test_cuenta_str(self):
        cuenta = Cuenta(nombre='Efectivo', slug='E')
        self.assertEqual(str(cuenta), 'Efectivo')

    def test_crear_crea_cuenta(self):
        Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual(Cuenta.cantidad(), 1)

    def test_crear_devuelve_cuenta_creada(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual((cuenta.nombre, cuenta.slug), ('Efectivo', 'e'))

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

    def test_opciones_deben_incluir_un_tipo(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        cuenta.opciones = ' '
        with self.assertRaises(ErrorOpciones):
            cuenta.full_clean()


class TestModelCuentaMetodos(TestCase):

    def setUp(self):
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(concepto='00000', importe=100, cta_entrada=self.cta1)


class TestModelCuentaPropiedades(TestModelCuentaMetodos):

    # @property tipo
    def test_tipo_devuelve_tipo_de_cuenta_segun_contenido_de_switches(self):
        self.assertEqual(self.cta1.tipo, 'interactiva')
        self.cta1.opciones = self.cta1.opciones.replace('i', 'c')
        self.cta1.save()
        self.assertEqual(self.cta1.tipo, 'caja')

    def test_tipo_da_error_si_no_hay_opcion_de_tipo(self):
        self.cta1.opciones = ' '
        self.cta1.save()
        with self.assertRaises(ErrorOpciones):
            tipo = self.cta1.tipo

    def test_tipo_agrega_y_retira_opciones_correctamente_al_ser_asignada(self):
        self.cta1.tipo = 'caja'
        self.cta1.save()
        self.assertIn('c', self.cta1.opciones)
        self.assertNotIn('i', self.cta1.opciones)
        self.cta1.tipo = 'interactiva'
        self.cta1.save()
        self.assertIn('i', self.cta1.opciones)
        self.assertNotIn('c', self.cta1.opciones)

    def test_tipo_da_error_si_se_le_asigna_valor_no_admitido(self):
        with self.assertRaises(ErrorOpciones):
            self.cta1.tipo = 'sanguche'

    # @property saldo:
    def test_saldo_devuelve_el_saldo_de_la_cuenta(self):
        self.assertEqual(self.cta1.saldo, self.cta1._saldo)

    def test_saldo_asigna_saldo_a_cuenta(self):
        self.cta1.saldo = 300
        self.assertEqual(self.cta1._saldo, 300)


class TestMetodosMovsYSaldos(TestModelCuentaMetodos):

    """ Después del setUp:
        self.cta1.saldo == 110
        self.cta2.saldo == 120
    """

    def setUp(self):
        super().setUp()
        self.cta2 = Cuenta.crear('Banco', 'B')
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


class TestMetodoDividir(TestModelCuentaMetodos):

    def setUp(self):
        super().setUp()
        Movimiento.crear(concepto='00000', importe=150, cta_entrada=self.cta1)
        self.subcuentas = [
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50},
             {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200},
        ]

    def test_genera_cuentas_a_partir_de_lista_de_diccionarios(self):
        self.cta1.dividir_entre(self.subcuentas)

        subcuenta1 = Cuenta.tomar(slug='ebil')
        subcuenta2 = Cuenta.tomar(slug='ecaj')

        self.assertEqual(subcuenta1.nombre, 'Billetera')
        self.assertEqual(subcuenta1.saldo, 50)
        self.assertEqual(subcuenta2.nombre, 'Cajón de arriba')
        self.assertEqual(subcuenta2.saldo, 200)

    def test_genera_movimientos_de_traspaso_entre_cta_madre_y_subcuentas(self):
        self.cta1.dividir_entre(self.subcuentas)

        subcuenta1 = Cuenta.tomar(slug='ebil')
        subcuenta2 = Cuenta.tomar(slug='ecaj')

        movs = Movimiento.todes()
        self.assertEqual(len(movs), 4)

        self.assertEqual(
            movs[2].concepto,
            'Paso de saldo de Efectivo a subcuenta Billetera'
        )
        self.assertEqual(movs[2].importe, 50)
        self.assertEqual(movs[2].cta_entrada, subcuenta1)
        self.assertEqual(movs[2].cta_salida, self.cta1)
        self.assertEqual(
            movs[3].concepto,
            'Paso de saldo de Efectivo a subcuenta Cajón de arriba'
        )
        self.assertEqual(movs[3].importe, 200)
        self.assertEqual(movs[3].cta_entrada, subcuenta2)
        self.assertEqual(movs[3].cta_salida, self.cta1)

    def test_cuenta_madre_se_convierte_en_caja(self):
        self.cta1.dividir_entre(self.subcuentas)
        self.assertNotEqual(self.cta1.tipo, "interactiva")
        self.assertEqual(self.cta1.tipo, "caja")

    def test_cuentas_generadas_son_subcuentas_de_cuenta_madre(self):
        self.cta1.dividir_entre(self.subcuentas)
        cta2 = Cuenta.tomar(slug='ebil')
        cta3 = Cuenta.tomar(slug='ecaj')

        self.assertEqual(cta2.cta_madre, self.cta1)
        self.assertEqual(cta3.cta_madre, self.cta1)

        self.assertEqual(list(self.cta1.subcuentas.all()), [cta2, cta3, ])

    def test_saldo_de_cta_madre_es_igual_a_la_suma_de_saldos_de_subcuentas(self):
        self.cta1.dividir_entre(self.subcuentas)

        cta2 = Cuenta.tomar(slug='ebil')
        cta3 = Cuenta.tomar(slug='ecaj')

        self.assertEqual(self.cta1.saldo, cta2.saldo + cta3.saldo)


class TestCuentaMadre(TestModelCuentaMetodos):

    def setUp(self):
        super().setUp()
        self.cta1.dividir_entre([
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 25},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 75},
        ])
        self.cta2 = Cuenta.tomar(slug='ebil')
        self.cta3 = Cuenta.tomar(slug='ecaj')

    def test_movimiento_en_subcuenta_se_refleja_en_saldo_de_cta_madre(self):

        saldo_cta1 = self.cta1.saldo

        Movimiento.crear(concepto='mov', importe=45, cta_entrada=self.cta2)
        self.cta1.refresh_from_db()
        self.assertEqual(
            self.cta1.saldo, saldo_cta1+45,
            'Mov de entrada en subcuenta no se refleja en saldo de cta madre'
        )

    def test_movimiento_en_subcuenta_se_refleja_en_saldo_de_cta_abuela(self):

        self.cta3.dividir_entre([
            {'nombre': 'Cajita', 'slug': 'eccj', 'saldo': 32},
            {'nombre': 'Sobre', 'slug': 'ecso', 'saldo': 53},
        ])
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
        self.fail('Testear!')

    def test_cuenta_caja_no_acepta_movimientos(self):
        with self.assertRaises(ValidationError):
            Movimiento.crear(
                concepto='mov', importe=100, cta_entrada=self.cta1
            )


class TestMetodosVarios(TestModelCuentaMetodos):

    def test_esta_en_una_caja_devuelve_true_si_tiene_cta_madre(self):
        self.cta1.dividir_entre([
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 40},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 60},
        ])

        cta2 = Cuenta.tomar(slug='ebil')
        cta3 = Cuenta.tomar(slug='ecaj')

        self.assertTrue(cta2.esta_en_una_caja())
        self.assertFalse(self.cta1.esta_en_una_caja())
