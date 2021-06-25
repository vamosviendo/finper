from datetime import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, Movimiento

from utils.errors import \
    SaldoNoCeroException, ErrorOpciones, ErrorDeSuma, ErrorTipo, \
    ErrorDependenciaCircular, ErrorCuentaEsInteractiva


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

    def test_cuenta_creada_tiene_saldo_cero_por_defecto(self):
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

    def test_slug_se_guarda_siempre_en_minusculas(self):
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

    def test_opciones_deben_incluir_un_tipo(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        cuenta.opciones = ' '
        with self.assertRaises(ErrorOpciones):
            cuenta.full_clean()

    def test_opciones_no_pueden_incluir_mas_de_un_tipo(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='e')
        cuenta.opciones = 'ic'
        with self.assertRaises(ErrorOpciones):
            cuenta.full_clean()


class TestModelCuentaCrear(TestCase):

    def test_crear_crea_cuenta(self):
        Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual(Cuenta.cantidad(), 1)

    def test_crear_devuelve_cuenta_creada(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.assertEqual((cuenta.nombre, cuenta.slug), ('Efectivo', 'e'))

    def test_crear_no_permite_nombre_vacio(self):
        with self.assertRaises(ValidationError):
            Cuenta.crear(nombre=None, slug='E')

    def test_genera_movimiento_inicial_si_se_pasa_argumento_saldo(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='e', saldo=155)
        self.assertEqual(Movimiento.cantidad(), 1)
        mov = Movimiento.primere()
        self.assertEqual(mov.concepto, f'Saldo inicial de {cuenta.nombre}')

    def test_no_genera_movimiento_si_no_se_pasa_argumento_saldo(self):
        Cuenta.crear('Efectivo', 'e')
        self.assertEqual(Movimiento.cantidad(), 0)

    def test_no_genera_movimiento_si_argumento_saldo_es_igual_a_cero(self):
        Cuenta.crear('Efectivo', 'e', saldo=0)
        self.assertEqual(Movimiento.cantidad(), 0)

    def test_importe_de_movimiento_generado_coincide_con_argumento_saldo(self):
        Cuenta.crear('Efectivo', 'e', saldo=232)
        mov = Movimiento.primere()
        self.assertEqual(mov.importe, 232)

    def test_cuenta_creada_es_cta_entrada_del_movimiento_generado(self):
        cuenta = Cuenta.crear('Efectivo', 'e', saldo=234)
        mov = Movimiento.primere()
        self.assertEqual(mov.cta_entrada, cuenta)

    def test_cuenta_creada_es_cta_salida_del_movimiento_generado_si_el_saldo_es_negativo(self):
        cuenta = Cuenta.crear('Efectivo', 'e', saldo=-354)
        mov = Movimiento.primere()
        self.assertIsNone(mov.cta_entrada)
        self.assertEqual(mov.cta_salida, cuenta)
        self.assertEqual(mov.importe, 354)

    def test_funciona_con_saldo_en_formato_str(self):
        cuenta = Cuenta.crear('Efectivo', 'e', saldo='354')
        self.assertEqual(cuenta.saldo, 354)


class TestModelCuentaMetodos(TestCase):
    """ Saldos después de setUp
        self.cta1: 100
    """

    def setUp(self):
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(concepto='00000', importe=100, cta_entrada=self.cta1)


class TestModelCuentaPropiedades(TestModelCuentaMetodos):
    """ Saldos después de setUp
        self.cta1: 100
    """

    # @property tipo
    def test_tipo_devuelve_tipo_de_cuenta_segun_contenido_de_switches(self):
        self.assertTrue(self.cta1.tipo, 'interactiva')
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
    """ Saldos después del setUp:
        self.cta1.saldo == 100-70+80 = 110
        self.cta2.saldo == 70+50 = 120
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

    def test_movs_devuelve_todos_los_movimientos_de_una_cuenta(self):
        movs_cta1 = [
            Movimiento.tomar(concepto='00000'),
            Movimiento.tomar(concepto='mov2'),
            Movimiento.tomar(concepto='mov3'),
        ]
        for mov in movs_cta1:
            self.assertIn(mov, self.cta1.movs())

    def test_movs_incluye_movimientos_de_subcuentas(self):
        subcuentas = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 30, },
            {'nombre': 'Cajoncito', 'slug': 'ec', }
        )
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

    def test_movs_devuelve_movimientos_ordenados_por_fecha(self):
        m1 = Movimiento.tomar(concepto='00000')
        m2 = Movimiento.tomar(concepto='mov2')
        m3 = Movimiento.tomar(concepto='mov3')
        m1.fecha = datetime(2021, 5, 25)
        m2.fecha = datetime(2020, 12, 2)
        m3.fecha = datetime(2021, 2, 28)
        for mov in [m1, m2, m3]:
            mov.save()

        self.assertEqual(
            list(self.cta1.movs()),
            [m2, m3, m1]
        )

    def test_cantidad_movs_devuelve_entradas_mas_salidas(self):
        self.assertEqual(self.cta1.cantidad_movs(), 3)

    def test_total_movs_devuelve_suma_importes_entradas_menos_salidas(self):
        self.assertEqual(self.cta1.total_movs(), 110)

    def test_total_subcuentas_devuelve_suma_saldos_subcuentas(self):
        self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 15},
            {'nombre': 'Cajón', 'slug': 'ec', 'saldo': 65},
            {'nombre': 'Cajita', 'slug': 'eca', }
        )
        cta2 = Cuenta.tomar(slug='eb')
        Movimiento.crear('Movimiento', 5, cta_salida=cta2)
        self.assertEqual(self.cta1.total_subcuentas(), 105)

    def test_total_subcuentas_tira_excepcion_si_cuenta_es_interactiva(self):
        with self.assertRaisesMessage(
                ErrorCuentaEsInteractiva,
                'Cuenta "Efectivo" es interactiva y como tal no tiene '
                'subcuentas'
        ):
            total = self.cta1.total_subcuentas()

    def test_saldo_ok_devuelve_true_si_saldo_coincide_con_movimientos_en_cuenta_interactiva(self):
        self.assertEqual(self.cta1.saldo, 110)
        self.assertTrue(self.cta1.saldo_ok())

    def test_saldo_ok_devuelve_true_si_saldo_coincide_con_saldos_subcuentas_en_cuenta_caja(self):
        self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 15},
            {'nombre': 'Cajón', 'slug': 'ec', }
        )
        self.assertEqual(self.cta1.saldo, 110)
        self.assertTrue(self.cta1.saldo_ok())

    def test_saldo_ok_devuelve_false_si_saldo_cta_interactiva_no_coincide_con_movimientos(self):
        self.cta1.saldo = 220
        self.cta1.save()
        self.assertFalse(self.cta1.saldo_ok())

    def test_saldo_ok_devuelve_false_si_saldo_cta_caja_no_coincide_con_saldos_subcuentas(self):
        self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 15},
            {'nombre': 'Cajón', 'slug': 'ec', }
        )
        self.cta1.saldo = 220
        self.cta1.save()
        self.assertFalse(self.cta1.saldo_ok())

    def test_corregir_saldo_corrige_saldo_a_partir_de_los_importes_de_movimientos(self):
        self.cta1.saldo = 345
        self.cta1.save()
        self.cta1.corregir_saldo()
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.saldo, self.cta1.total_movs())

    def test_corregir_saldo_corrige_a_partir_de_saldos_de_subcuentas_en_cuentas_caja(self):
        self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 15},
            {'nombre': 'Cajón', 'slug': 'ec', 'saldo': 65},
            {'nombre': 'Cajita', 'slug': 'eca', }
        )
        cta2 = Cuenta.tomar(slug='eb')
        Movimiento.crear('Movimiento', 5, cta_salida=cta2)
        self.cta1.saldo = 550
        self.cta1.save()
        self.cta1.corregir_saldo()
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.saldo, self.cta1.total_subcuentas())

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

    def test_agregar_mov_correctivo_no_acepta_ctas_caja(self):
        self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'eb', 'saldo': 15},
            {'nombre': 'Cajón', 'slug': 'ec', }
        )
        self.cta1.saldo = 945
        self.cta1.save()
        with self.assertRaises(ValidationError):
            self.cta1.agregar_mov_correctivo()

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


class TestMetodoDividirEntre(TestModelCuentaMetodos):
    """ Saldos después de setUp:
        self.cta1: 100+150 = 250
        self.cta1.subcuentas.get(slug='ebil'): 50
        self.cta1.subcuentas.get(slug='ecaj'): 200
    """

    def setUp(self):
        super().setUp()
        Movimiento.crear(concepto='00000', importe=150, cta_entrada=self.cta1)
        self.subcuentas = [
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200},
        ]

    def test_genera_cuentas_a_partir_de_lista_de_diccionarios(self):
        self.cta1.dividir_entre(*self.subcuentas)

        subcuenta1 = Cuenta.tomar(slug='ebil')
        subcuenta2 = Cuenta.tomar(slug='ecaj')

        self.assertEqual(subcuenta1.nombre, 'Billetera')
        self.assertEqual(subcuenta2.nombre, 'Cajón de arriba')

    def test_cuentas_generadas_son_subcuentas_de_cuenta_madre(self):
        self.cta1.dividir_entre(*self.subcuentas)
        cta2 = Cuenta.tomar(slug='ebil')
        cta3 = Cuenta.tomar(slug='ecaj')

        self.assertEqual(cta2.cta_madre, self.cta1)
        self.assertEqual(cta3.cta_madre, self.cta1)

        self.assertEqual(list(self.cta1.subcuentas.all()), [cta2, cta3, ])

    def test_devuelve_lista_con_subcuentas_creadas(self):
        self.assertEqual(
            self.cta1.dividir_entre(*self.subcuentas),
            [Cuenta.tomar(slug='ebil'), Cuenta.tomar(slug='ecaj')]
        )

    def test_genera_movimientos_de_traspaso_entre_cta_madre_y_subcuentas(self):
        self.cta1.dividir_entre(*self.subcuentas)

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

    def test_acepta_mas_de_dos_subcuentas(self):
        self.subcuentas[1]['saldo'] = 130
        self.subcuentas.append(
            {'nombre': 'Cajita', 'slug':'ecjt', 'saldo': 70})

        self.cta1.dividir_entre(*self.subcuentas)

        self.assertEqual(self.cta1.subcuentas.count(), 3)
        self.assertEqual(
            sum([cta.saldo for cta in self.cta1.subcuentas.all()]),
            250
        )

    def test_cuenta_madre_se_convierte_en_caja(self):
        self.cta1.dividir_entre(*self.subcuentas)
        self.assertFalse(self.cta1.es_interactiva)
        self.assertTrue(self.cta1.es_caja)

    def test_saldo_de_cta_madre_es_igual_a_la_suma_de_saldos_de_subcuentas(self):
        self.cta1.dividir_entre(*self.subcuentas)

        cta2 = Cuenta.tomar(slug='ebil')
        cta3 = Cuenta.tomar(slug='ecaj')

        self.assertEqual(self.cta1.saldo, cta2.saldo + cta3.saldo)

    def test_acepta_y_completa_una_subcuenta_sin_saldo(self):
        self.subcuentas[1]['saldo'] = 130
        self.subcuentas.append({'nombre': 'Cajita', 'slug': 'ecjt'})

        self.cta1.dividir_entre(*self.subcuentas)

        cta = Cuenta.tomar(slug='ecjt')

        self.assertEqual(self.cta1.subcuentas.count(), 3)
        self.assertEqual(cta.saldo, 70)

    def test_no_acepta_mas_de_una_subcuenta_sin_saldo(self):
        self.subcuentas[0]['saldo'] = 250
        self.subcuentas[1].pop('saldo')
        self.subcuentas.append({'nombre': 'Cajita', 'slug': 'ecjt'})

        with self.assertRaises(ErrorDeSuma):
            self.cta1.dividir_entre(*self.subcuentas)

    def test_da_error_si_suma_de_saldos_subcuentas_no_coinciden_con_saldo(self):
        self.subcuentas[1]['saldo'] = 235

        with self.assertRaisesMessage(
                ErrorDeSuma,
                "Suma errónea. Saldos de subcuentas deben sumar 250.00"
        ):
            self.cta1.dividir_entre(*self.subcuentas)

    def test_acepta_saldos_en_formato_str(self):
        self.subcuentas[0]['saldo'] = '50'
        self.subcuentas[1]['saldo'] = '200'

        subcuentas_creadas = self.cta1.dividir_entre(self.subcuentas)

        self.assertEqual(subcuentas_creadas[0].saldo, 50.0)
        self.assertEqual(subcuentas_creadas[1].saldo, 200.0)

    def test_acepta_saldos_en_distintos_formatos(self):
        self.subcuentas[0]['saldo'] = 50
        self.subcuentas[1]['saldo'] = '200'

        subcuentas_creadas = self.cta1.dividir_entre(self.subcuentas)

    def test_acepta_una_cuenta_sin_saldo_con_saldos_en_formato_str(self):
        self.subcuentas[0]['saldo'] = '50'
        self.subcuentas[1]['saldo'] = '130'
        self.subcuentas.append({'nombre': 'Cajita', 'slug': 'ecjt'})

        self.cta1.dividir_entre(*self.subcuentas)

        cta_nueva = Cuenta.tomar(slug='ecjt')

        self.assertEqual(cta_nueva.saldo, 70.0)

    def test_funciona_con_lista_de_dicts(self):
        self.cta1.dividir_entre(self.subcuentas)   # No debe dar error

    def test_funciona_con_tuplas_o_listas_con_nombre_slug_y_saldo(self):
        subctas = self.cta1.dividir_entre(
            ('Billetera', 'ebil', 50), ('Cajón de arriba', 'ecaj', 200))
        self.assertEqual(subctas[0].nombre, 'Billetera')
        self.assertEqual(subctas[1].nombre, 'Cajón de arriba')

        self.assertEqual(subctas[0].slug, 'ebil')
        self.assertEqual(subctas[1].slug, 'ecaj')

        self.assertEqual(subctas[0].saldo, 50.0)
        self.assertEqual(subctas[1].saldo, 200.0)

    def test_funciona_con_listas(self):
        subctas = self.cta1.dividir_entre(
            ['Billetera', 'ebil', 50], ['Cajón de arriba', 'ecaj', 200])
        self.assertEqual(subctas[0].nombre, 'Billetera')
        self.assertEqual(subctas[1].nombre, 'Cajón de arriba')

        self.assertEqual(subctas[0].slug, 'ebil')
        self.assertEqual(subctas[1].slug, 'ecaj')

        self.assertEqual(subctas[0].saldo, 50.0)
        self.assertEqual(subctas[1].saldo, 200.0)

    def test_funciona_con_tupla_y_lista(self):
        subctas = self.cta1.dividir_entre(
            ('Billetera', 'ebil', 50), ['Cajón de arriba', 'ecaj', 200])
        self.assertEqual(subctas[0].nombre, 'Billetera')
        self.assertEqual(subctas[1].nombre, 'Cajón de arriba')

    def test_funciona_con_tupla_y_dict(self):
        subctas = self.cta1.dividir_entre(
            ('Billetera', 'ebil', 50),
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200}
        )
        self.assertEqual(subctas[0].nombre, 'Billetera')
        self.assertEqual(subctas[1].nombre, 'Cajón de arriba')

    def test_funciona_con_tupla_de_tuplas(self):
        subctas = self.cta1.dividir_entre(
            (('Billetera', 'ebil', 50), ['Cajón de arriba', 'ecaj', 200]))
        self.assertEqual(subctas[0].nombre, 'Billetera')
        self.assertEqual(subctas[1].nombre, 'Cajón de arriba')

    def test_acepta_una_tupla_sin_saldo(self):
        subctas = self.cta1.dividir_entre(
            ('Billetera', 'ebil', 50), ('Cajón de arriba', 'ecaj'))
        self.assertEqual(subctas[0].nombre, 'Billetera')
        self.assertEqual(subctas[1].nombre, 'Cajón de arriba')
        self.assertEqual(subctas[1].saldo, 200)

    def test_no_acepta_mas_de_una_tupla_sin_saldo(self):
        with self.assertRaises(ErrorDeSuma):
            subctas = self.cta1.dividir_entre(
                ('Billetera', 'ebil', 50),
                ('Cajón de arriba', 'ecaj'),
                ('Cajón de abajo', 'ecab')
            )


class TestCuentaMadre(TestModelCuentaMetodos):
    """ Saldos después de setUp
        self.cta1: 100
        self.cta2: 25
        self.cta3: 75
    """

    def setUp(self):
        super().setUp()
        self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 25},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 75},
        )
        self.cta2 = Cuenta.tomar(slug='ebil')
        self.cta3 = Cuenta.tomar(slug='ecaj')

    def test_cuenta_caja_debe_tener_subcuentas(self):
        self.cta2.tipo = 'caja'
        with self.assertRaises(ErrorTipo):
            self.cta2.full_clean()

    def test_cuenta_interactiva_no_puede_tener_subcuentas(self):
        self.cta1.tipo = 'interactiva'
        with self.assertRaises(ErrorTipo):
            self.cta1.full_clean()

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

    def test_cuenta_interactiva_no_puede_ser_asignada_como_madre(self):
        cta4 = Cuenta.crear('Caja', 'c')
        cta4.cta_madre = self.cta2
        with self.assertRaisesMessage(
                ErrorTipo,
                'Cuenta interactiva "Billetera" no puede ser madre'
        ):
            cta4.full_clean()

    def test_si_se_asigna_cta_interactiva_con_saldo_a_cta_caja_se_suma_el_saldo(self):
        saldo_cta1 = self.cta1.saldo
        cta4 = Cuenta.crear("Bolsillo", "ebol", saldo=50)

        cta4.cta_madre = self.cta1
        cta4.save()

        self.assertEqual(cta4.saldo, 50)
        self.assertEqual(self.cta1.saldo, saldo_cta1 + 50)

    def test_si_se_asigna_cta_caja_con_saldo_a_cta_caja_se_suma_el_saldo(self):
        saldo_cta1 = self.cta1.saldo
        cta4 = Cuenta.crear("Bolsillos", "ebol", saldo=50)

        cta4.dividir_entre(
            {'nombre': 'Bolsillo campera', 'slug': 'ebca', 'saldo': 30},
            {'nombre': 'Bolsillo pantalón', 'slug': 'ebpa'}
        )

        cta4.cta_madre = self.cta1
        cta4.save()

        self.assertEqual(cta4.saldo, 50)
        self.assertEqual(self.cta1.saldo, saldo_cta1 + 50)

    def test_cuenta_no_puede_ser_subcuenta_de_una_de_sus_subcuentas(self):
        cta4 = Cuenta.crear("Bolsillos", "ebol")
        cta4.dividir_entre(
            {'nombre': 'Bolsillo campera', 'slug': 'ebca', 'saldo': 0},
            {'nombre': 'Bolsillo pantalón', 'slug': 'ebpa'}
        )
        cta4.cta_madre = self.cta1
        cta4.save()

        self.cta1.cta_madre = cta4
        with self.assertRaisesMessage(
                ErrorDependenciaCircular,
                'Cuenta madre Bolsillos está entre las subcuentas de Efectivo '
                'o entre las de una de sus subcuentas'
        ):
            self.cta1.full_clean()

    def test_cuenta_no_puede_ser_subcuenta_de_una_subcuenta_de_una_de_sus_subcuentas(self):
        cta4 = Cuenta.crear("Bolsillos", "ebol")
        cta4.dividir_entre(
            {'nombre': 'Bolsillo campera', 'slug': 'ebca', 'saldo': 0},
            {'nombre': 'Bolsillo pantalón', 'slug': 'ebpa'}
        )

        cta4.cta_madre = self.cta1
        cta4.save()

        cta5 = Cuenta.tomar(slug='ebpa')
        cta5.dividir_entre(
            {
                'nombre': 'Bolsillo delantero pantalón',
                'slug': 'ebpd',
                'saldo': 0
            },
            {'nombre': 'Bolsillo pantalón trasero', 'slug': 'ebpt'}
        )

        self.cta1.cta_madre = cta5
        with self.assertRaisesMessage(
                ErrorDependenciaCircular,
                'Cuenta madre Bolsillo pantalón está entre las subcuentas '
                'de Efectivo o entre las de una de sus subcuentas'
        ):
            self.cta1.full_clean()

    def test_movimiento_en_subcuenta_se_refleja_en_saldo_de_cta_madre(self):

        saldo_cta1 = self.cta1.saldo

        Movimiento.crear(concepto='mov', importe=45, cta_entrada=self.cta2)
        self.cta1.refresh_from_db()
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

        self.cta3.dividir_entre(
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
        saldo_cta1 = self.cta1.saldo
        mov = Movimiento.crear('mov', 45, self.cta2)
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.saldo, saldo_cta1+45)

        mov.importe = 55
        mov.save()
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.saldo, saldo_cta1+55)

        cta4 = Cuenta.crear('Otro banco', 'ob')
        mov.cta_entrada = cta4
        mov.save()
        self.cta1.refresh_from_db()
        self.assertEqual(self.cta1.saldo, saldo_cta1)

        mov.cta_entrada = self.cta2
        mov.cta_salida = self.cta1
        mov.importe = 40
        self.assertEqual(self.cta1.saldo, saldo_cta1)

    def test_cuenta_caja_no_acepta_movimientos(self):
        with self.assertRaises(ValidationError):
            Movimiento.crear(
                concepto='mov', importe=100, cta_entrada=self.cta1
            )


class TestMetodosVarios(TestModelCuentaMetodos):

    def test_esta_en_una_caja_devuelve_true_si_tiene_cta_madre(self):
        self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 40},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 60},
        )

        cta2 = Cuenta.tomar(slug='ebil')
        cta3 = Cuenta.tomar(slug='ecaj')

        self.assertTrue(cta2.esta_en_una_caja())
        self.assertFalse(self.cta1.esta_en_una_caja())

    def test_arbol_de_subcuentas_devuelve_set_con_todas_las_cuentas_dependientes(self):
        lista_subcuentas = self.cta1.dividir_entre(
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 0},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', },
        )
        lista_subcuentas += lista_subcuentas[0].dividir_entre(
            {
                'nombre': 'Billetera división delantera',
                'slug': 'ebdd',
                'saldo': 0,
            },
            {'nombre': 'Billetera división trasera', 'slug': 'ebdt', },
        )
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
        lista_subcuentas += lista_subcuentas[1].dividir_entre(
            {
                'nombre': 'Cajita verde',
                'slug': 'eccv',
                'saldo': 0,
            },
            {'nombre': 'Sobre', 'slug': 'ecs', },
        )

        self.assertEqual(
            self.cta1.arbol_de_subcuentas(), set(lista_subcuentas))
