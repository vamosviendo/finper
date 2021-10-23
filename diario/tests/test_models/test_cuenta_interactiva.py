from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import \
    Cuenta, Movimiento, CuentaInteractiva, CuentaAcumulativa, Titular
from diario.settings_app import TITULAR_PRINCIPAL
from utils.errors import ErrorDeSuma, ErrorMovimientoPosteriorAConversion


class TestModelCuentaInteractiva(TestCase):

    def test_se_relaciona_con_titular(self):
        tit = Titular.crear(titname='tito', nombre='Tito Gómez')
        cuenta = CuentaInteractiva(nombre='cuenta', slug='cta')
        cuenta.titular = tit
        cuenta.full_clean()
        cuenta.save()

        self.assertEqual(cuenta.titular, tit)

    def test_toma_titular_por_defecto(self):
        cuenta = CuentaInteractiva(nombre='cuenta', slug='cta')

        cuenta.full_clean()
        cuenta.save()

        self.assertEqual(
            cuenta.titular,
            Titular.tomar(titname=TITULAR_PRINCIPAL['titname'])
        )


class TestModelCuentaInteractivaCrear(TestCase):

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

    def test_cuenta_creada_con_saldo_positivo_es_cta_entrada_del_movimiento_generado(self):
        cuenta = Cuenta.crear('Efectivo', 'e', saldo=234)
        mov = Movimiento.primere()
        self.assertEqual(
            mov.cta_entrada,
            Cuenta.tomar(polymorphic=False, pk=cuenta.pk)
        )

    def test_cuenta_creada_con_saldo_negativo_es_cta_salida_del_movimiento_generado(self):
        cuenta = Cuenta.crear('Efectivo', 'e', saldo=-354)
        mov = Movimiento.primere()
        self.assertIsNone(mov.cta_entrada)
        self.assertEqual(
            mov.cta_salida,
            Cuenta.tomar(polymorphic=False, pk=cuenta.pk)
        )
        self.assertEqual(mov.importe, 354)

    def test_puede_pasarse_saldo_en_formato_str(self):
        cuenta = Cuenta.crear('Efectivo', 'e', saldo='354')
        self.assertEqual(cuenta.saldo, 354)


class TestMetodoDividirEntre(TestCase):
    """ Saldos después de setUp:
        self.cta1: 100+150 = 250
        self.cta1.subcuentas.get(slug='ebil'): 50
        self.cta1.subcuentas.get(slug='ecaj'): 200
    """

    def setUp(self):
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )
        Movimiento.crear(
            concepto='00000', importe=150, cta_entrada=self.cta1,
            fecha=date(2019, 1, 1)
        )
        self.subcuentas = [
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200},
        ]

    @patch('diario.models.cuenta.CuentaInteractiva.saldo_ok')
    def test_verifica_saldo_cuenta_antes_de_dividirla(self, mock_saldo_ok):
        self.cta1.dividir_entre(*self.subcuentas)
        mock_saldo_ok.assert_called_once()

    @patch('diario.models.cuenta.CuentaInteractiva.saldo_ok')
    def test_da_error_si_saldo_no_ok(self, mock_saldo_ok):
        mock_saldo_ok.return_value = False
        with self.assertRaisesMessage(
                ValidationError,
                'Saldo de cuenta "efectivo" no coincide '
                'con sus movimientos. Verificar'

        ):
            self.cta1.dividir_entre(*self.subcuentas)

    def test_genera_cuentas_a_partir_de_lista_de_diccionarios(self):
        self.cta1.dividir_entre(*self.subcuentas)

        subcuenta1 = Cuenta.tomar(slug='ebil')
        subcuenta2 = Cuenta.tomar(slug='ecaj')

        self.assertEqual(subcuenta1.nombre, 'billetera')
        self.assertEqual(subcuenta2.nombre, 'cajón de arriba')

    def test_cuentas_generadas_son_subcuentas_de_cuenta_madre(self):
        self.cta1 = self.cta1.dividir_y_actualizar(*self.subcuentas)
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

    def test_genera_movimientos_de_salida_en_cta_madre(self):
        self.cta1.dividir_entre(*self.subcuentas)

        Cuenta.tomar(slug='ebil')
        Cuenta.tomar(slug='ecaj')

        movs = self.cta1.movs_directos()

        self.assertEqual(len(movs), 4)

        self.assertEqual(
            movs[2].concepto,
            'Saldo pasado por Efectivo a nueva subcuenta Billetera'
        )
        self.assertEqual(movs[2].importe, 50)
        # self.assertEqual(movs[2].cta_entrada, subcuenta1)
        self.assertEqual(movs[2].cta_salida, self.cta1)
        self.assertEqual(
            movs[3].concepto,
            'Saldo pasado por Efectivo a nueva subcuenta Cajón de arriba'
        )
        self.assertEqual(movs[3].importe, 200)
        # self.assertEqual(movs[3].cta_entrada, subcuenta2)
        self.assertEqual(movs[3].cta_salida, self.cta1)

    def test_agrega_subcuenta_como_cta_entrada_en_movimiento(self):
        self.cta1.dividir_entre(*self.subcuentas)

        movs = self.cta1.movs_directos()

        for i, mov in enumerate(movs[2:]):
            self.assertEqual(
                mov.cta_entrada.como_subclase(),
                Cuenta.tomar(slug=self.subcuentas[i]['slug'])
            )

    def test_acepta_mas_de_dos_subcuentas(self):
        self.subcuentas[1]['saldo'] = 130
        self.subcuentas.append(
            {'nombre': 'Cajita', 'slug':'ecjt', 'saldo': 70})

        self.cta1 = self.cta1.dividir_y_actualizar(*self.subcuentas)

        self.assertEqual(self.cta1.subcuentas.count(), 3)
        self.assertEqual(
            sum([cta.saldo for cta in self.cta1.subcuentas.all()]),
            250
        )

    def test_cuenta_madre_se_convierte_en_acumulativa(self):
        pk = self.cta1.pk
        self.cta1.dividir_entre(*self.subcuentas)
        self.cta1 = Cuenta.tomar(pk=pk)

        self.assertFalse(self.cta1.es_interactiva)
        self.assertTrue(self.cta1.es_acumulativa)

    def test_guarda_fecha_de_conversion_en_cuenta_madre(self):
        pk = self.cta1.pk
        self.cta1.dividir_entre(*self.subcuentas)
        self.cta1 = Cuenta.tomar(pk=pk)

        self.assertEqual(self.cta1.fecha_conversion, date.today())

    def test_acepta_fecha_de_conversion_distinta_de_la_actual(self):
        pk = self.cta1.pk
        self.cta1.dividir_entre(*self.subcuentas, fecha=date(2020, 10, 5))
        self.cta1 = Cuenta.tomar(pk=pk)

        self.assertEqual(self.cta1.fecha_conversion, date(2020, 10, 5))

    def test_movimientos_tienen_fecha_igual_a_la_de_conversion(self):
        fecha = date(2020, 10, 5)
        self.cta1.dividir_entre(*self.subcuentas, fecha=fecha)
        traspaso1 = Movimiento.tomar(
            concepto="Saldo pasado por Efectivo a nueva subcuenta Billetera")
        traspaso2 = Movimiento.tomar(concepto="Saldo pasado por Efectivo a nue"
                                              "va subcuenta Cajón de arriba")
        self.assertEqual(traspaso1.fecha, fecha)
        self.assertEqual(traspaso2.fecha, fecha)

    def test_no_acepta_fecha_de_conversion_anterior_a_la_de_cualquier_movimiento_de_la_cuenta(self):
        fecha = date(2020, 1, 1)
        Movimiento.crear(
            'movimiento posterior', 100, self.cta1, fecha=date(2020, 5, 5))
        Movimiento.crear(
            'movimiento posterior', 100, None, self.cta1,
            fecha=date(2020, 6, 5)
        )
        self.cta1.refresh_from_db()

        with self.assertRaises(ErrorMovimientoPosteriorAConversion):
            self.cta1.dividir_entre(*self.subcuentas, fecha=fecha)

    def test_saldo_de_cta_madre_es_igual_a_la_suma_de_saldos_de_subcuentas(self):
        self.cta1.dividir_entre(*self.subcuentas)

        cta2 = Cuenta.tomar(slug='ebil')
        cta3 = Cuenta.tomar(slug='ecaj')

        self.cta1 = Cuenta.tomar(slug=self.cta1.slug)

        self.assertEqual(self.cta1.saldo, cta2.saldo + cta3.saldo)

    def test_acepta_y_completa_una_subcuenta_sin_saldo(self):
        self.subcuentas[1]['saldo'] = 130
        self.subcuentas.append({'nombre': 'Cajita', 'slug': 'ecjt'})

        self.cta1 = self.cta1.dividir_y_actualizar(*self.subcuentas)

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
        self.assertEqual(subctas[0].nombre, 'billetera')
        self.assertEqual(subctas[1].nombre, 'cajón de arriba')

        self.assertEqual(subctas[0].slug, 'ebil')
        self.assertEqual(subctas[1].slug, 'ecaj')

        self.assertEqual(subctas[0].saldo, 50.0)
        self.assertEqual(subctas[1].saldo, 200.0)

    def test_funciona_con_listas(self):
        subctas = self.cta1.dividir_entre(
            ['Billetera', 'ebil', 50], ['Cajón de arriba', 'ecaj', 200])
        self.assertEqual(subctas[0].nombre, 'billetera')
        self.assertEqual(subctas[1].nombre, 'cajón de arriba')

        self.assertEqual(subctas[0].slug, 'ebil')
        self.assertEqual(subctas[1].slug, 'ecaj')

        self.assertEqual(subctas[0].saldo, 50.0)
        self.assertEqual(subctas[1].saldo, 200.0)

    def test_funciona_con_tupla_y_lista(self):
        subctas = self.cta1.dividir_entre(
            ('Billetera', 'ebil', 50), ['Cajón de arriba', 'ecaj', 200])
        self.assertEqual(subctas[0].nombre, 'billetera')
        self.assertEqual(subctas[1].nombre, 'cajón de arriba')

    def test_funciona_con_tupla_y_dict(self):
        subctas = self.cta1.dividir_entre(
            ('Billetera', 'ebil', 50),
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200}
        )
        self.assertEqual(subctas[0].nombre, 'billetera')
        self.assertEqual(subctas[1].nombre, 'cajón de arriba')

    def test_funciona_con_tupla_de_tuplas(self):
        subctas = self.cta1.dividir_entre(
            (('Billetera', 'ebil', 50), ['Cajón de arriba', 'ecaj', 200]))
        self.assertEqual(subctas[0].nombre, 'billetera')
        self.assertEqual(subctas[1].nombre, 'cajón de arriba')

    def test_acepta_una_tupla_sin_saldo(self):
        subctas = self.cta1.dividir_entre(
            ('Billetera', 'ebil', 50), ('Cajón de arriba', 'ecaj'))
        self.assertEqual(subctas[0].nombre, 'billetera')
        self.assertEqual(subctas[1].nombre, 'cajón de arriba')
        self.assertEqual(subctas[1].saldo, 200)

    def test_no_acepta_mas_de_una_tupla_sin_saldo(self):
        with self.assertRaises(ErrorDeSuma):
            self.cta1.dividir_entre(
                ('Billetera', 'ebil', 50),
                ('Cajón de arriba', 'ecaj'),
                ('Cajón de abajo', 'ecab')
            )


class TestConvertirseEnAcumulativa(TestCase):

    def test_convertirse_en_acumulativa_convierte_cuenta_interactiva_en_acumulativa(self):
        cta_int = CuentaInteractiva.crear('Efectivo', 'efec')
        pk_cta_int = cta_int.pk

        cta_int._convertirse_en_acumulativa()

        cta_acum = Cuenta.tomar(pk=pk_cta_int)

        self.assertIsInstance(cta_acum, CuentaAcumulativa)
        self.assertNotIsInstance(cta_acum, CuentaInteractiva)

    def test_convertirse_en_acumulativa_acepta_fecha_distinta_de_la_actual(self):
        cta_int = CuentaInteractiva.crear('Efectivo', 'efec')
        pk_cta_int = cta_int.pk

        cta_int._convertirse_en_acumulativa(fecha=date(2020, 5, 2))

        cta_acum = Cuenta.tomar(pk=pk_cta_int)
        self.assertEqual(cta_acum.fecha_conversion, date(2020, 5, 2))

    def test_cuenta_convertida_conserva_movimientos(self):
        cta_int = CuentaInteractiva.crear('Efectivo', 'efec', saldo=1000)
        pk_cta_int = cta_int.pk
        Movimiento.crear('salida', 1500, cta_salida=cta_int)
        Movimiento.crear('entrada', 500, cta_entrada=cta_int)

        cta_int._convertirse_en_acumulativa()

        cta_acum = CuentaAcumulativa.tomar(pk=pk_cta_int)

        self.assertEqual(cta_acum.cantidad_movs(), 3)

    def test_cuenta_convertida_conserva_nombre(self):
        cta_int = CuentaInteractiva.crear('Efectivo', 'efec')
        pk_cta_int = cta_int.pk
        nombre_cta_int = cta_int.nombre

        cta_acum = cta_int._convertirse_en_acumulativa()
        self.assertEqual(cta_acum.nombre, nombre_cta_int)

    def test_devuelve_cuenta_convertida(self):
        cta_int = CuentaInteractiva.crear('Efectivo', 'efec')
        pk_cta_int = cta_int.pk

        cta_acum = cta_int._convertirse_en_acumulativa()

        self.assertEqual(
            CuentaAcumulativa.tomar(pk=pk_cta_int),
            cta_acum
        )


class TestVaciarSaldo(TestCase):

    def test_genera_movimientos_con_fecha_recibida(self):
        fecha = date(2020, 5, 4)
        cta_int = CuentaInteractiva.crear('Efectivo', 'efec')
        ctas_limpias = cta_int._ajustar_subcuentas(
            [['subc1', 'sc1', 10], ['subc2', 'sc2']])
        cta_int._vaciar_saldo(ctas_limpias, fecha=fecha)
        traspaso1 = Movimiento.tomar(
            concepto="Saldo pasado por Efectivo a nueva subcuenta Subc1")
        traspaso2 = Movimiento.tomar(
            concepto="Saldo pasado por Efectivo a nueva subcuenta Subc2")
        self.assertEqual(traspaso1.fecha, fecha)
        self.assertEqual(traspaso2.fecha, fecha)

    def test_genera_movimientos_con_fecha_de_hoy_si_no_se_pasa_fecha(self):
        cta_madre = CuentaInteractiva.crear('Efectivo', 'efec')
        ctas_limpias = cta_madre._ajustar_subcuentas(
            [['subc1', 'sc1', 10], ['subc2', 'sc2']])

        movimientos = cta_madre._vaciar_saldo(ctas_limpias)

        self.assertEqual(movimientos[0].fecha, date.today())
        self.assertEqual(movimientos[1].fecha, date.today())

    def test_trunca_conceptos_excesivamente_largos_a_la_longitud_maxima(self):
        cta_madre = CuentaInteractiva.crear(
            'Caja de ahorro Banco Nación', 'cabn')
        ctas_limpias = cta_madre._ajustar_subcuentas([
            ['caja de ahorro banco nación propia pero no tan propia porque '
             'en realidad la comparto', 'cabp', 10],
            ['caja de ahorro banco nación ajena tralararí '
             'tralarará chipoteo chipoteo fumanchú', 'caba'],
        ])
        maxlength = Movimiento.get_max_length('concepto')

        movimientos = cta_madre._vaciar_saldo(ctas_limpias)

        self.assertEqual(len(movimientos[0].concepto), maxlength)
        self.assertEqual(len(movimientos[1].concepto), maxlength)


class TestSaldoOk(TestCase):

    def test_saldo_ok_devuelve_true_si_saldo_coincide_con_movimientos_en_cuenta_interactiva(self):
        cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=cta1,
            fecha=date(2019, 1, 1)
        )
        self.assertEqual(cta1.saldo, 100)
        self.assertTrue(cta1.saldo_ok())

    def test_saldo_ok_devuelve_false_si_saldo_cta_interactiva_no_coincide_con_movimientos(self):
        cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=cta1,
            fecha=date(2019, 1, 1)
        )
        cta1.saldo = 220
        cta1.save()
        self.assertFalse(cta1.saldo_ok())


class TestCorregirSaldo(TestCase):

    def test_corregir_saldo_corrige_saldo_a_partir_de_los_importes_de_movimientos(self):
        cta1 = Cuenta.crear('Efectivo', 'E')
        Movimiento.crear(
            concepto='00000',
            importe=100,
            cta_entrada=cta1,
            fecha=date(2019, 1, 1)
        )
        cta1.saldo = 345
        cta1.save()
        cta1.corregir_saldo()
        cta1.refresh_from_db()
        self.assertEqual(cta1.saldo, cta1.total_movs())