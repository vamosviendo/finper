from datetime import date, timedelta
from unittest.mock import patch, call

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, CuentaInteractiva, Movimiento, Titular
from utils import errors
from utils.helpers_tests import dividir_en_dos_subcuentas


class TestModelMovimiento(TestCase):

    def setUp(self):
        self.titular1 = Titular.crear(nombre='Titular 1', titname='tit1')
        self.cuenta1 = Cuenta.crear(nombre='Cuenta titular 1', slug='ct1', titular=self.titular1)


class TestModelMovimientoBasic(TestModelMovimiento):

    def test_guarda_y_recupera_movimientos(self):
        primer_mov = Movimiento()
        primer_mov.fecha = date.today()
        primer_mov.concepto = 'entrada de efectivo'
        primer_mov.importe = 985.5
        primer_mov.cta_entrada = self.cuenta1
        primer_mov.save()

        segundo_mov = Movimiento()
        segundo_mov.fecha = date(2021, 4, 28)
        segundo_mov.concepto = 'compra en efectivo'
        segundo_mov.detalle = 'salchichas, pan, mostaza'
        segundo_mov.importe = 500
        segundo_mov.cta_salida = self.cuenta1
        segundo_mov.save()

        movs_guardados = Movimiento.todes()
        self.assertEqual(movs_guardados.count(), 2)

        primer_mov_guardado = Movimiento.tomar(pk=primer_mov.pk)
        segundo_mov_guardado = Movimiento.tomar(pk=segundo_mov.pk)

        self.assertEqual(primer_mov_guardado.fecha, date.today())
        self.assertEqual(primer_mov_guardado.concepto, 'entrada de efectivo')
        self.assertEqual(primer_mov_guardado.importe, 985.5)
        self.assertEqual(primer_mov_guardado.cta_entrada, self.cuenta1)

        self.assertEqual(segundo_mov_guardado.fecha, date(2021, 4, 28))
        self.assertEqual(segundo_mov_guardado.concepto, 'compra en efectivo')
        self.assertEqual(
            segundo_mov_guardado.detalle, 'salchichas, pan, mostaza')
        self.assertEqual(segundo_mov_guardado.importe, 500)
        self.assertEqual(segundo_mov_guardado.cta_salida, self.cuenta1)

    def test_cta_entrada_se_relaciona_con_cuenta(self):
        mov = Movimiento(
            fecha=date.today(), concepto='Cobranza en efectivo', importe=100)
        mov.cta_entrada = self.cuenta1
        mov.save()
        self.assertIn(mov, self.cuenta1.entradas.all())

    def test_cta_salida_se_relaciona_con_cuenta(self):
        mov = Movimiento(
            fecha=date.today(), concepto='Cobranza en efectivo', importe=100)
        mov.cta_salida = self.cuenta1
        mov.save()
        self.assertIn(mov, self.cuenta1.salidas.all())

    def test_permite_guardar_cuentas_de_entrada_y_salida_en_un_movimiento(self):
        cuenta2 = Cuenta.crear(nombre='Banco', slug='B')
        mov = Movimiento(
            fecha=date.today(),
            concepto='Retiro de efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=cuenta2
        )

        mov.full_clean()    # No debe dar error
        mov.save()

        self.assertIn(mov, self.cuenta1.entradas.all())
        self.assertIn(mov, cuenta2.salidas.all())
        self.assertNotIn(mov, self.cuenta1.salidas.all())
        self.assertNotIn(mov, cuenta2.entradas.all())

    def test_movimientos_se_ordenan_por_fecha(self):
        mov1 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Pago en efectivo',
            importe=100,
            cta_salida=self.cuenta1,
        )
        mov2 = Movimiento.crear(
            fecha=date(2021, 4, 2),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
        )
        mov3 = Movimiento.crear(
            fecha=date(2020, 10, 22),
            concepto='Cobranza en efectivo',
            importe=243,
            cta_entrada=self.cuenta1,
        )

        self.assertEqual(list(Movimiento.todes()), [mov3, mov2, mov1])

    def test_dentro_de_fecha_movimientos_se_ordenan_por_campo_orden_dia(self):
        mov1 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Mov1',
            importe=100,
            cta_salida=self.cuenta1,
        )
        mov2 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Mov2',
            importe=100,
            cta_entrada=self.cuenta1,
        )
        mov3 = Movimiento.crear(
            fecha=date(2021, 5, 3),
            concepto='Mov3',
            importe=243,
            cta_entrada=self.cuenta1,
        )

        mov3.orden_dia = 0
        mov3.full_clean()
        mov3.save()
        mov1.refresh_from_db()
        mov2.refresh_from_db()

        self.assertEqual(list(Movimiento.todes()), [mov3, mov1, mov2])


class TestModelMovimientoCrear(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear(
            nombre='Banco', slug='b', titular=self.titular1)

    def test_no_admite_cuenta_acumulativa(self):
        self.cuenta1 = self.cuenta1.dividir_y_actualizar(
            ['subcuenta 1', 'sc1', 0],
            ['subcuenta 2', 'sc2']
        )
        with self.assertRaises(errors.ErrorCuentaEsAcumulativa):
            Movimiento.crear(
                concepto='Cobranza en efectivo',
                importe=100,
                cta_entrada=self.cuenta1
            )

    def test_guarda_fecha_de_hoy_por_defecto(self):
        mov = Movimiento.crear(
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1
        )
        self.assertEqual(mov.fecha, date.today())

    def test_funciona_con_args_basicos_sin_nombre(self):
        mov1 = Movimiento.crear('Pago en efectivo', 100, None, self.cuenta1)
        mov2 = Movimiento.crear('Cobranza en efectivo', 100, self.cuenta1)
        mov3 = Movimiento.crear(
            'Extracción bancaria', 50, self.cuenta1, self.cuenta2)
        self.assertEqual(mov1.concepto, 'Pago en efectivo')
        self.assertIsNone(mov1.cta_entrada)
        self.assertEqual(mov2.cta_entrada, self.cuenta1)
        self.assertIsNone(mov2.cta_salida)
        self.assertEqual(mov3.cta_salida, self.cuenta2)

    def test_funciona_con_argumentos_mixtos(self):
        mov1 = Movimiento.crear(
            'Pago en efectivo', 100, None, self.cuenta1,
            fecha=date(2020, 10, 22),
        )
        mov2 = Movimiento.crear(
            'Cobranza en efectivo', 100, self.cuenta1, detalle='Alquiler')
        mov3 = Movimiento.crear(
            'Pago en efectivo', 100, cta_salida=self.cuenta1)

        self.assertEqual(mov1.fecha, date(2020, 10, 22))
        self.assertEqual(mov2.detalle, 'Alquiler')
        self.assertIsNone(mov2.cta_salida)
        self.assertEqual(mov3.cta_salida, self.cuenta1)
        self.assertIsNone(mov3.cta_entrada)

    def test_mov_entrada_con_importe_negativo_se_crea_como_mov_salida(self):
        mov = Movimiento.crear('Pago', -100, cta_entrada=self.cuenta1)
        self.assertIsNone(mov.cta_entrada)
        self.assertEqual(mov.cta_salida, self.cuenta1)

    def test_mov_salida_con_importe_negativo_se_crea_como_mov_entrada(self):
        mov = Movimiento.crear('Pago', -100, cta_salida=self.cuenta1)
        self.assertIsNone(mov.cta_salida)
        self.assertEqual(mov.cta_entrada, self.cuenta1)

    def test_mov_traspaso_con_importe_negativo_intercambia_cta_entrada_y_salida(self):
        mov = Movimiento.crear(
            'Pago', -100, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertEqual(mov.cta_salida, self.cuenta2)
        self.assertEqual(mov.cta_entrada, self.cuenta1)

    def test_mov_con_importe_negativo_se_crea_con_importe_positivo(self):
        mov = Movimiento.crear('Pago', -100, cta_entrada=self.cuenta1)
        self.assertEqual(mov.importe, 100)

    def test_importe_cero_tira_error(self):
        with self.assertRaisesMessage(
                errors.ErrorImporteCero,
                "Se intentó crear un movimiento con importe cero"
        ):
            Movimiento.crear('Pago', 0, cta_salida=self.cuenta1)

    def test_acepta_importe_en_formato_str(self):
        mov = Movimiento.crear('Pago', '200', cta_entrada=self.cuenta1)
        self.assertEqual(mov.importe, 200.0)


class TestModelMovimientoCrearModificaSaldosDeCuentas(TestModelMovimiento):
    """ Saldos después de setUp:
        self.cuenta1: 125.0
        self.cuenta2: -35.0
    """

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear('Banco', 'B', titular=self.titular1)
        self.saldo1 = self.cuenta1.saldo
        self.saldo2 = self.cuenta2.saldo
        self.mov1 = Movimiento.crear(
            fecha=date.today(),
            concepto='Carga de saldo',
            importe=125,
            cta_entrada=self.cuenta1
        )
        self.mov2 = Movimiento.crear(
            fecha=date.today(),
            concepto='Transferencia a otra cuenta',
            importe=35,
            cta_salida=self.cuenta2
        )

    def test_suma_importe_a_cta_entrada(self):
        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov1.importe)

    def test_resta_importe_de_cta_salida(self):
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov2.importe)

    def test_puede_traspasar_saldo_de_una_cuenta_a_otra(self):
        saldo1 = self.cuenta1.saldo
        saldo2 = self.cuenta2.saldo

        mov3 = Movimiento.crear(
            concepto='Depósito',
            importe=50,
            cta_entrada=self.cuenta2,
            cta_salida=self.cuenta1
        )
        self.assertEqual(self.cuenta2.saldo, saldo2+mov3.importe)
        self.assertEqual(self.cuenta1.saldo, saldo1-mov3.importe)


class TestModelMovimientoEntreTitulares(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.titular2 = Titular.crear(titname='tit2', nombre='Titular 2')
        self.cuenta2 = Cuenta.crear(
            'Cuenta titular 2', 'ct2', titular=self.titular2)


class TestModelModelMovimientoEntreTitularesPrimero(
        TestModelMovimientoEntreTitulares):

    @patch.object(Cuenta, 'crear')
    def test_genera_cuentas_credito_si_no_existen(self, mock_crear):
        mock_crear.side_effect = [
            CuentaInteractiva(nombre='mock0', slug='mock0'),
            CuentaInteractiva(nombre='mock1', slug='mock1'),
        ]

        Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)

        self.assertEqual(
            mock_crear.call_args_list[0],
            call(
                nombre='Préstamo entre tit2 y tit1',
                slug='_tit2-tit1',
                titular=self.titular2
            )
        )
        args2 = mock_crear.call_args_list[1][1]
        args2.pop('contracuenta')
        self.assertEqual(
            args2,
            dict(
                nombre='Préstamo entre tit1 y tit2',
                slug='_tit1-tit2',
                titular=self.titular1,
            )
        )

    @patch.object(Cuenta, 'crear')
    def test_no_genera_nada_si_esgratis(self, mock_crear):
        Movimiento.crear(
            'Prestamo', 10,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2,
            esgratis=True
        )
        mock_crear.assert_not_called()

    def test_genera_movimiento_contrario_entre_cuentas_credito(self):
        Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        self.assertEqual(Movimiento.cantidad(), 2)

        cuenta_deudora = Cuenta.tomar(slug='_tit1-tit2')
        cuenta_acreedora = Cuenta.tomar(slug='_tit2-tit1')
        mov_credito = Movimiento.tomar(concepto='Constitución de crédito')
        self.assertEqual(mov_credito.detalle, 'de Titular 2 a Titular 1')
        self.assertEqual(mov_credito.importe, 10)
        self.assertEqual(mov_credito.cta_entrada, cuenta_acreedora)
        self.assertEqual(mov_credito.cta_salida, cuenta_deudora)

    def test_guarda_marcador_al_movimiento_de_credito_generado(self):
        movimiento = Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        mov_credito = Movimiento.tomar(concepto='Constitución de crédito')
        self.assertEqual(movimiento.id_contramov, mov_credito.id)

    def test_integrativo_genera_cuenta_credito_y_subcuentas_y_movimiento(self):
        movimiento = Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        self.assertEqual(Cuenta.cantidad(), 4)
        self.assertEqual(Movimiento.cantidad(), 2)

        cuenta_deudora = Cuenta.tomar(slug='_tit1-tit2')
        cuenta_acreedora = Cuenta.tomar(slug='_tit2-tit1')
        self.assertEqual(cuenta_acreedora.saldo, movimiento.importe)
        self.assertEqual(cuenta_deudora.saldo, -cuenta_acreedora.saldo)

        mov_credito = Movimiento.tomar(concepto='Constitución de crédito')
        self.assertEqual(mov_credito.importe, movimiento.importe)
        self.assertEqual(
            mov_credito.cta_entrada.titular,
            movimiento.cta_salida.titular
        )
        self.assertEqual(
            mov_credito.cta_salida.titular,
            movimiento.cta_entrada.titular
        )

    def test_incluye_titular_cta_receptora_entre_los_deudores_de_titular_cta_emisora(self):
        Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        self.assertIn(self.titular1, self.titular2.deudores.all())

    def test_incluye_titular_cta_emisora_entre_los_acreedores_de_titular_cta_deudora(self):
        Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        self.assertIn(self.titular2, self.titular1.acreedores.all())

    def test_integrativo_no_genera_nada_si_esgratis(self):
        Movimiento.crear(
            'Prestamo', 10,
            cta_entrada=self.cuenta1, cta_salida=self.cuenta2,
            esgratis=True
        )
        self.assertEqual(Cuenta.cantidad(), 2)
        self.assertEqual(Movimiento.cantidad(), 1)


class TestModelMovimientoEntreTitularesSiguientes(
        TestModelMovimientoEntreTitulares):

    def setUp(self):
        super().setUp()
        Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)

    @patch.object(Movimiento, '_generar_cuentas_credito')
    def test_no_crea_cuentas_de_credito_si_ya_existen_entre_los_titulares(self, mock_generar_cuentas_credito):
        mock_generar_cuentas_credito.return_value = (
            Cuenta(nombre='mock1', slug='mock1'),
            Cuenta(nombre='mock2', slug='mock2')
        )
        Movimiento.crear(
            'Prestamo', 15, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        mock_generar_cuentas_credito.assert_not_called()

    @patch.object(Movimiento, '_generar_cuentas_credito')
    def test_no_crea_cuentas_credito_en_movimiento_inverso_entre_titulares_con_credito_existente(
            self, mock_generar_cuentas_credito):
        mock_generar_cuentas_credito.return_value = (
            Cuenta(nombre='mock1', slug='mock1'),
            Cuenta(nombre='mock2', slug='mock2')
        )
        Movimiento.crear(
            'Devolución', 6, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        mock_generar_cuentas_credito.assert_not_called()

    def test_resta_importe_de_cuenta_credito_en_movimiento_inverso_entre_titulares_con_credito_existente(self):
        Movimiento.crear('Devolución', 6, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertEqual(Cuenta.tomar(slug='_tit2-tit1').saldo, 4)

    def test_suma_importe_a_cuenta_deuda_en_movimiento_inverso_entre_titulares_con_credito_existente(self):
        Movimiento.crear('Devolución', 6, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertEqual(Cuenta.tomar(slug='_tit1-tit2').saldo, -4)

    def test_da_cuenta_en_el_concepto_de_un_aumento_de_credito(self):
        Movimiento.crear(
            'Prestamo', 15, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        self.assertEqual(Movimiento.todes()[2].concepto, 'Aumento de crédito')

    def test_da_cuenta_en_el_concepto_de_una_devolucion_parcial(self):
        Movimiento.crear(
            'Devolución', 6, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertEqual(
            Movimiento.todes()[2].concepto,
            'Pago a cuenta de crédito'
        )

    def test_da_cuenta_en_el_concepto_de_una_cancelacion_de_credito(self):
        Movimiento.crear(
            'Devolución', 10, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertEqual(
            Movimiento.todes()[2].concepto,
            'Cancelación de crédito'
        )

    def test_si_es_un_pago_a_cuenta_no_incluye_emisor_entre_acreedores_de_receptor(self):
        Movimiento.crear(
            'A cuenta', 3, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertNotIn(self.titular1, self.titular2.acreedores.all())

    def test_si_es_un_pago_a_cuenta_mantiene_emisor_entre_deudores_de_receptor(self):
        Movimiento.crear(
            'A cuenta', 3, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertIn(self.titular1, self.titular2.deudores.all())

    @patch.object(Titular, 'cancelar_deuda_de', autospec=True)
    def test_si_cancela_deuda_elimina_emisor_de_deudores_de_receptor(self, mock_cancelar_deuda_de):
        Movimiento.crear(
            'Devolución', 10, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        mock_cancelar_deuda_de.assert_called_once_with(self.titular2, self.titular1)

    def test_si_paga_mas_de_lo_que_debe_elimina_emisor_de_deudores_de_receptor(self):
        Movimiento.crear(
            'Devolución', 16, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertNotIn(self.titular1, self.titular2.deudores.all())

    def test_si_paga_mas_de_lo_que_debe_incluye_receptor_entre_deudores_de_emisor(self):
        Movimiento.crear(
            'Devolución', 16, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertIn(self.titular2, self.titular1.deudores.all())


class TestModelMovimientoClean(TestModelMovimiento):

    def test_requiere_al_menos_una_cuenta(self):
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100
        )
        with self.assertRaisesMessage(
                ValidationError, errors.CUENTA_INEXISTENTE
        ):
            mov.full_clean()

    def test_no_admite_misma_cuenta_de_entrada_y_de_salida(self):
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta1
        )
        with self.assertRaisesMessage(ValidationError, errors.CUENTAS_IGUALES):
            mov.full_clean()

    def test_permite_movimientos_duplicados(self):
        Movimiento.crear(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1
        )
        mov = Movimiento(
            fecha=date.today(),
            concepto='Cobranza en efectivo',
            importe=100,
            cta_entrada=self.cuenta1
        )
        mov.full_clean()    # No debe dar error


class TestModelMovimientoModificar(TestModelMovimiento):
    """ Saldos después de setUp:
        self.cuenta1: 125.0+50 = 175
        self.cuenta2: -35.0-50 = -85
    """

    def setUp(self):
        super().setUp()
        self.cuenta2 = Cuenta.crear('cuenta 2', 'c2', titular=self.titular1)
        self.titular2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta3 = Cuenta.crear(
            nombre='Cuenta de tit2', slug='ct2', titular=self.titular2)
        self.mov1 = Movimiento.crear(
            fecha=date(2021, 1, 5),
            concepto='entrada',
            importe=125,
            cta_entrada=self.cuenta1,
        )
        self.mov2 = Movimiento.crear(
            concepto='salida',
            importe=35,
            cta_salida=self.cuenta1
        )
        self.mov3 = Movimiento.crear(
            concepto='traspaso',
            importe=50,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2
        )
        self.saldo1 = self.cuenta1.saldo
        self.saldo2 = self.cuenta2.saldo
        self.imp1 = self.mov1.importe
        self.imp2 = self.mov2.importe
        self.imp3 = self.mov3.importe

    def refresh_ctas(self, *args):
        self.cuenta1.refresh_from_db()
        self.cuenta2.refresh_from_db()
        self.cuenta3.refresh_from_db()
        for arg in args:
            arg.refresh_from_db()


class TestModelMovimientoEliminar(TestModelMovimientoModificar):
    """ Saldos después de setUp:
        self.cuenta1: 125.0+50 = 175
        self.cuenta2: -35.0-50 = -85
    """

    def test_eliminar_movimiento_resta_de_saldo_cta_entrada_y_suma_a_saldo_cta_salida(self):

        self.mov1.delete()
        self.cuenta1.refresh_from_db(fields=['_saldo'])

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp1)
        saldo1 = self.cuenta1.saldo

        self.mov3.delete()
        self.cuenta1.refresh_from_db(fields=['_saldo'])
        self.cuenta2.refresh_from_db(fields=['_saldo'])

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(self.cuenta1.saldo, saldo1-self.imp3)

    @patch.object(Movimiento, '_eliminar_contramovimiento', autospec=True)
    def test_eliminar_movimiento_con_contramovimiento_elimina_contramovimiento(
            self, mock_eliminar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        movimiento.delete()
        mock_eliminar_contramovimiento.assert_called_once_with(movimiento)

    def test_eliminar_movimiento_con_contramovimiento_repone_saldo_de_cuentas_credito(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        cta_deudora = contramov.cta_salida
        cta_acreedora = contramov.cta_entrada

        movimiento.delete()

        cta_deudora.refresh_from_db(fields=['_saldo'])
        cta_acreedora.refresh_from_db(fields=['_saldo'])
        self.assertEqual(cta_deudora.saldo, 0)
        self.assertEqual(cta_acreedora.saldo, 0)


class TestModelMovimientoModificarGeneral(TestModelMovimientoModificar):

    def test_no_modifica_saldo_de_cuentas_si_no_se_modifica_importe_ni_cuentas(self):
        self.mov3.concepto = 'Depósito en efectivo'
        self.mov3.save()

        self.cuenta1.refresh_from_db()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2)

    @patch.object(Movimiento, '_regenerar_contramovimiento')
    def test_en_movimiento_con_contramovimiento_no_regenera_contramovimiento_si_se_modifica_concepto(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.concepto = 'Prastamo'
        movimiento.save()

        mock_regenerar_contramovimiento.assert_not_called()

    @patch.object(Movimiento, '_regenerar_contramovimiento')
    def test_en_movimiento_con_contramovimiento_no_regenera_contramovimiento_si_se_modifica_detalle(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.detalle = 'El titular 1 le presta al titular 2 30 pesotes'
        movimiento.save()

        mock_regenerar_contramovimiento.assert_not_called()

    @patch.object(Movimiento, '_regenerar_contramovimiento')
    def test_en_movimiento_con_contramovimiento_no_regenera_contramovimiento_si_se_modifica_orden_dia(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.orden_dia -= 1
        movimiento.save()

        mock_regenerar_contramovimiento.assert_not_called()

    @patch.object(Movimiento, '_regenerar_contramovimiento', autospec=True)
    def test_en_movimiento_con_contramovimiento_regenera_contramovimiento_si_se_modifica_fecha(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.fecha = date(2020, 2, 23)
        movimiento.save()

        mock_regenerar_contramovimiento.assert_called_once_with(movimiento)


class TestModelMovimientoModificarImporte(TestModelMovimientoModificar):

    def test_resta_importe_antiguo_y_suma_el_nuevo_a_cta_entrada(self):
        self.mov1.importe = 128
        self.mov1.save()
        self.cuenta1.refresh_from_db()
        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1+self.mov1.importe)

    def test_suma_importe_antiguo_y_resta_el_nuevo_a_cta_salida(self):
        self.mov2.importe = 37
        self.mov2.save()
        self.cuenta1.refresh_from_db()
        self.assertEqual(
            self.cuenta1.saldo, self.saldo1+self.imp2-self.mov2.importe)

    def test_en_mov_traspaso_actua_sobre_las_dos_cuentas(self):
        """ Resta importe antiguo y suma nuevo a cta_entrada
            Suma importe antiguo y resta nuevo a cta_salida"""
        self.mov3.importe = 60
        self.mov3.save()
        self.refresh_ctas()
        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3+self.mov3.importe)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3-self.mov3.importe)

    @patch.object(Movimiento, '_regenerar_contramovimiento', autospec=True)
    def test_en_movimientos_con_contramovimiento_elimina_contramovimiento_para_volver_a_generarlo(
            self, mock_regenerar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.importe = 45
        movimiento.save()

        mock_regenerar_contramovimiento.assert_called_once_with(movimiento)

    def test_en_mov_traspaso_con_contramov_cambia_importe_contramov(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.importe = 45
        movimiento.save()

        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        self.assertEqual(contramov.importe, 45)

    def test_en_mov_traspaso_con_contramov_cambia_saldo_en_las_cuentas_del_contramov(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        cta_deudora = contramov.cta_salida
        cta_acreedora = contramov.cta_entrada

        movimiento.importe = 45
        movimiento.save()

        cta_deudora.refresh_from_db(fields=['_saldo'])
        cta_acreedora.refresh_from_db(fields=['_saldo'])
        self.assertEqual(cta_deudora.saldo, -45)
        self.assertEqual(cta_acreedora.saldo, 45)


class TestModelMovimientoModificarCuentas(TestModelMovimientoModificar):

    def test_modificar_cta_entrada_resta_importe_de_saldo_cuenta_anterior_y_lo_suma_a_cuenta_nueva(self):
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_modificar_cta_salida_suma_importe_a_saldo_cuenta_anterior_y_lo_resta_de_cuenta_nueva(self):
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()
        self.refresh_ctas()
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov2.importe)
        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)

    def test_modificar_cta_entrada_funciona_en_movimientos_de_traspaso(self):
        """ Resta importe de cta_entrada vieja y lo suma a la nueva."""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)
        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)

    @patch.object(Movimiento, '_regenerar_contramovimiento', autospec=True)
    def test_cambiar_cta_entrada_por_cta_otro_titular_en_movimientos_con_contramovimiento_regenera_contramovimiento(
            self, mock_regenerar_contramovimiento):
        titular = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta4 = Cuenta.crear(
            nombre='Cuenta tit3', slug='ct3', titular=titular)
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.cta_entrada = cuenta4
        movimiento.save()

        mock_regenerar_contramovimiento.assert_called_once_with(movimiento)

    def test_cambiar_cta_entrada_por_cta_otro_titular_en_movimiento_de_traspaso_con_contramovimiento_modifica_contramovimiento(self):
        titular = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta4 = Cuenta.crear(
            nombre='Cuenta tit3', slug='ct3', titular=titular)
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        cta_deudora = contramov.cta_salida

        movimiento.cta_entrada = cuenta4
        movimiento.save()

        contramov = Movimiento.tomar(id=movimiento.id_contramov)

        self.assertNotEqual(contramov.cta_salida.id, cta_deudora.id)
        self.assertEqual(contramov.cta_salida.slug, '_tit3-tit1')

    @patch.object(Movimiento, '_regenerar_contramovimiento', autospec=True)
    def test_cambiar_cta_salida_por_cta_otro_titular_en_movimientos_con_contramovimiento_regenera_contramovimiento(
            self, mock_regenerar_contramovimiento):
        titular = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta4 = Cuenta.crear(
            nombre='Cuenta tit3', slug='ct3', titular=titular)
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.cta_salida = cuenta4
        movimiento.save()

        mock_regenerar_contramovimiento.assert_called_once_with(movimiento)

    def test_cambiar_cta_salida_por_cta_otro_titular_en_movimiento_de_traspaso_con_contramovimiento_modifica_contramovimiento(self):
        titular = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta4 = Cuenta.crear(
            nombre='Cuenta tit3', slug='ct3', titular=titular)
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        cta_deudora = contramov.cta_salida

        movimiento.cta_salida = cuenta4
        movimiento.save()

        contramov = Movimiento.tomar(id=movimiento.id_contramov)

        self.assertNotEqual(contramov.cta_entrada.id, cta_deudora.id)
        self.assertEqual(contramov.cta_entrada.slug, '_tit3-tit2')

    @patch.object(Movimiento, '_crear_movimiento_credito', autospec=True)
    def test_cambiar_cta_entrada_por_cta_otro_titular_en_movimiento_de_traspaso_sin_contramovimiento_genera_contramovimiento(
            self, mock_crear_movimiento_credito):
        self.mov3.cta_entrada = self.cuenta3
        self.mov3.save()

        mock_crear_movimiento_credito.assert_called_once_with(self.mov3)

    @patch.object(Movimiento, '_crear_movimiento_credito', autospec=True)
    def test_cambiar_cta_salida_por_cta_otro_titular_en_movimiento_de_traspaso_sin_contramovimiento_genera_contramovimiento(
            self, mock_crear_movimiento_credito):
        self.mov3.cta_salida = self.cuenta3
        self.mov3.save()

        mock_crear_movimiento_credito.assert_called_once_with(self.mov3)

    @patch.object(Movimiento, '_eliminar_contramovimiento', autospec=True)
    def test_cambiar_cta_entrada_por_cta_mismo_titular_de_cta_salida_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento(
            self, mock_eliminar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento.cta_entrada = self.cuenta2
        movimiento.save()

        mock_eliminar_contramovimiento.assert_called_once_with(movimiento)

    def test_cambiar_cta_entrada_por_cta_mismo_titular_de_cta_salida_en_movimiento_de_traspaso_con_contramovimiento_no_regenera_contramovimiento_destruido(
            self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        with patch.object(Movimiento, '_crear_movimiento_credito') \
                as mock_crear_movimiento_credito:
            movimiento.cta_entrada = self.cuenta2
            movimiento.save()

            mock_crear_movimiento_credito.assert_not_called()

    def test_cambiar_cta_salida_por_cta_mismo_titular_de_cta_entrada_en_movimiento_de_traspaso_con_contramovimiento_destruye_contramovimiento(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta3)
        id_contramovimiento = movimiento.id_contramov

        movimiento.cta_salida = self.cuenta2
        movimiento.save()

        with self.assertRaises(Movimiento.DoesNotExist):
            Movimiento.tomar(id=id_contramovimiento)

    def test_cambiar_cta_salida_por_cta_mismo_titular_de_cta_entrada_en_movimiento_de_traspaso_con_contramovimiento_no_regenera_contramovimiento_destruido(
            self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta3)

        with patch.object(Movimiento, '_crear_movimiento_credito') \
                as mock_crear_movimiento_credito:
            movimiento.cta_salida = self.cuenta2
            movimiento.save()

            mock_crear_movimiento_credito.assert_not_called()

    def test_modificar_cta_salida_funciona_en_movimientos_de_traspaso(self):
        """ Suma importe a cta_salida vieja y lo suma a la nueva"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        self.mov3.cta_salida = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)

    def test_modificar_ambas_cuentas_funciona_en_movimientos_de_traspaso(self):
        """ Resta importe a cta_entrada vieja y lo suma a la nueva
            Suma importe a cta_salida vieja y lo suma a la nueva"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        cuenta4 = Cuenta.crear('Colchón', 'c')
        saldo3 = cuenta3.saldo
        saldo4 = cuenta4.saldo

        self.mov3.cta_entrada = cuenta3
        self.mov3.cta_salida = cuenta4
        self.mov3.save()
        self.refresh_ctas(cuenta3, cuenta4)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)
        self.assertEqual(cuenta4.saldo, saldo4-self.mov3.importe)

    def test_intercambiar_cuentas_resta_importe_x2_de_cta_entrada_y_lo_suma_a_cta_salida(self):
        """ Resta dos veces importe de vieja cta_entrada (ahora cta_salida)
            Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov3.cta_salida = self.cuenta1
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2 + self.mov3.importe*2)
        self.assertEqual(self.cuenta1.saldo, self.saldo1 - self.mov3.importe*2)

    def test_cuenta_de_salida_pasa_a_ser_de_entrada(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1 + self.mov2.importe*2)

    def test_cuenta_de_entrada_pasa_a_ser_de_salida(self):
        """ Resta dos veces importe a vieja cta_entrada (ahora cta_salida)"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1 - self.mov1.importe*2)

    def test_cuenta_de_salida_pasa_a_ser_de_entrada_y_cuenta_nueva_de_salida(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)
            Resta importe de nueva cta_salida"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe*2)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)

    def test_cuenta_de_entrada_pasa_a_ser_de_salida_y_cuenta_nueva_de_entrada(self):
        """ Resta dos veces importe a vieja cta_entrada (ahora cta_salida
            Suma importe a nueva cta_entrada """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta3
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe*2)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)

    def test_cuenta_de_salida_desaparece(self):
        """ Suma importe a cta_salida retirada"""
        self.mov3.cta_salida = None
        self.mov3.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)

    def test_cuenta_de_entrada_desaparece(self):
        """ Resta importe a cta_entrada retirada"""
        self.mov3.cta_entrada = None
        self.mov3.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida(self):
        """ Suma importe a cta_salida retirada
            Resta dos veces a vieja cta_entrada (ahora cta_salida) """
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe*2)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada(self):
        """ Resta importe a cta_entrada retirada
            Suma dos veces importe a vieja cta_salida (ahora cta_entrada)"""
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov3.importe*2)

    def test_aparece_cuenta_de_salida(self):
        """ Resta importe de nueva cta_salida """
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_aparece_cuenta_de_entrada(self):
        """ Suma importe a nueva cta_entrada """
        self.mov2.cta_entrada = self.cuenta1
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada(self):
        """ Resta dos veces importe de vieja cta_entrada (ahora cta_salida)
            Suma importe a nueva cta_entrada"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov1.importe*2)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida(self):
        """ Suma dos veces importe a vieja cta_salida (ahora cta_entrada)
            Resta importe de nueva cta_salida """
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta2
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov2.importe)
        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe*2)

    def test_desaparece_cta_entrada_y_aparece_cta_de_salida(self):
        """ Resta importe de cta_entrada retirada
            Resta importe de cta_salida agregada """
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_desaparece_cta_salida_y_aparece_cta_de_entrada(self):
        """ Suma importe a cta_salida retirada
            Suma importe a cta_entrada agregada"""
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.cta_salida = None
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov2.importe)
        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.mov2.importe)


class TestModelMovimientoModificarVariosCampos(TestModelMovimientoModificar):

    def test_cambia_cuenta_de_entrada_con_nuevo_importe(self):
        """ Resta viejo importe de cta_entrada vieja
            Suma nuevo importe a cta_entrada nueva """
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 128
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cambia_cuenta_de_salida_con_nuevo_importe(self):
        """ Suma viejo importe a cta_salida vieja
            Resta nuevo importe de cta_salida nueva """
        self.mov2.cta_salida = self.cuenta2
        self.mov2.importe = 63
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov2.importe)
        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.imp2)

    def test_cambia_cuenta_de_entrada_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Resta importe viejo de cta_entrada vieja
            Suma importe nuevo a cta_entrada nueva
            Suma importe viejo y resta importe nuevo a cta_salida """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_entrada = cuenta3
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)
        self.assertEqual(
            self.cuenta2.saldo,
            self.saldo2+self.imp3-self.mov3.importe
        )

    def test_cambia_cuenta_de_salida_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida vieja
            Resta importe nuevo de cta_salida nueva
            Resta importe viejo y suma importe nuevo a cta_entrada """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)
        self.assertEqual(
            self.cuenta1.saldo,
            self.saldo1-self.imp3+self.mov3.importe
        )

    def test_cambian_ambas_cuentas_en_mov_de_traspaso_con_nuevo_importe(self):
        """ Resta importe viejo de cta_entrada vieja
            Suma importe nuevo a cta_entrada nueva
            Suma importe viejo a cta_salida vieja
            Suma importe nuevo a cta_entrada nueva """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo
        cuenta4 = Cuenta.crear('Colchón', 'ch')
        saldo4 = cuenta4.saldo

        self.mov3.cta_entrada = cuenta3
        self.mov3.cta_salida = cuenta4
        self.mov3.importe = 56
        self.mov3.save()
        self.refresh_ctas(cuenta3, cuenta4)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)
        self.assertEqual(cuenta4.saldo, saldo4-self.mov3.importe)

    def test_se_intercambian_cuentas_de_entrada_y_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo de cta_entrada vieja
                (ahora cta_salida)
            Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada) """
        self.mov3.cta_entrada = self.cuenta2
        self.mov3.cta_salida = self.cuenta1
        self.mov3.importe = 456
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3-self.mov3.importe)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3+self.mov3.importe)

    def test_cta_entrada_pasa_a_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a cta_entrada vieja
                (ahora cta_salida)"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = None
        self.mov1.importe = 128
        self.mov1.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1-self.mov1.importe)

    def test_cta_salida_pasa_a_entrada_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada) """
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = None
        self.mov2.importe = 128
        self.mov2.save()
        self.cuenta1.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1+self.imp2+self.mov2.importe)

    def test_cta_salida_pasa_entrada_y_cta_salida_nueva_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a cta_salida vieja
                (ahora cta_entrada)
            Resta importe viejo de cta_entrada vieja
            Suma importe nuevo a cta_entrada nueva """
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = cuenta3
        self.mov3.importe = 252
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3+self.mov3.importe)
        self.assertEqual(cuenta3.saldo, saldo3-self.mov3.importe)

    def test_cta_entrada_pasa_salida_y_cta_entrada_nueva_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a cta_entrada vieja
                (ahora cta_salida)
            Resta importe viejo de cta_salida vieja
            Suma importe nuevo a cta_entrada nueva"""
        cuenta3 = Cuenta.crear('Cuenta corriente', 'cc')
        saldo3 = cuenta3.saldo

        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = cuenta3
        self.mov3.importe = 165
        self.mov3.save()
        self.refresh_ctas(cuenta3)

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)
        self.assertEqual(cuenta3.saldo, saldo3+self.mov3.importe)

    def test_cuenta_de_salida_desaparece_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida retirada
            Resta importe viejo y suma importe nuevo a cta_entrada"""
        self.mov3.cta_salida = None
        self.mov3.importe = 234
        self.mov3.save()
        self.cuenta2.refresh_from_db()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3+self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)

    def test_cuenta_de_entrada_desaparece_con_nuevo_importe(self):
        """ Resta importe viejo a cta_entrada retirada
            Suma importe viejo y resta importe nuevo a cta_salida"""
        self.mov3.cta_entrada = None
        self.mov3.importe = 234
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3-self.mov3.importe)

    def test_cuenta_de_salida_desaparece_y_cuenta_de_entrada_pasa_a_salida_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo a vieja cta_entrada
                (ahora cta_salida)
            Suma importe viejo a cta_salida retirada """
        self.mov3.cta_salida = self.mov3.cta_entrada
        self.mov3.cta_entrada = None
        self.mov3.importe = 350
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp3-self.mov3.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.imp3)

    def test_cuenta_de_entrada_desaparece_y_cuenta_de_salida_pasa_a_entrada_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo a vieja cta_salida
                (ahora cta_entrada)
            Resta importe viejo a cta_entrada retirada """
        self.mov3.cta_entrada = self.mov3.cta_salida
        self.mov3.cta_salida = None
        self.mov3.importe = 354
        self.mov3.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp3)
        self.assertEqual(
            self.cuenta2.saldo, self.saldo2+self.imp3+self.mov3.importe)

    def test_aparece_cuenta_de_salida_con_nuevo_importe(self):
        """ Resta importe viejo y suma importe nuevo a cta_entrada
            Resta importe nuevo a cta_salida nueva"""
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 255
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1+self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_aparece_cuenta_de_entrada_con_nuevo_importe(self):
        """ Suma importe viejo y resta importe nuevo a cta_salida
            Suma importe nuevo a cta_entrada nueva"""
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.importe = 446
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov2.importe)
        self.assertEqual(
            self.cuenta1.saldo, self.saldo1+self.imp2-self.mov2.importe)

    def test_cuenta_de_entrada_pasa_a_salida_y_aparece_nueva_cuenta_de_entrada_con_nuevo_importe(self):
        """ Resta importe viejo e importe nuevo de antigua cta_entrada
                (ahora cta_salida)
            Suma importe nuevo a cta_entrada agregada"""
        self.mov1.cta_salida = self.mov1.cta_entrada
        self.mov1.cta_entrada = self.cuenta2
        self.mov1.importe = 556
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(
            self.cuenta1.saldo, self.saldo1-self.imp1-self.mov1.importe)
        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov1.importe)

    def test_cuenta_de_salida_pasa_a_entrada_y_aparece_nueva_cuenta_de_salida_con_nuevo_importe(self):
        """ Suma importe viejo e importe nuevo de antigua cta_salida
                (ahora cta_entrada)
            Resta importe nuevo de cta_salida nueva """
        self.mov2.cta_entrada = self.mov2.cta_salida
        self.mov2.cta_salida = self.cuenta2
        self.mov2.importe = 445
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov2.importe)
        self.assertEqual(
            self.cuenta1.saldo, self.saldo1+self.imp2+self.mov2.importe)

    def test_desaparece_cta_entrada_y_aparece_otra_cta_de_salida_con_nuevo_importe(self):
        """ Resta importe viejo de cta_entrada retirada
            Resta importe nuevo de cta_salida agregada """
        self.mov1.cta_entrada = None
        self.mov1.cta_salida = self.cuenta2
        self.mov1.importe = 565
        self.mov1.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta1.saldo, self.saldo1-self.imp1)
        self.assertEqual(self.cuenta2.saldo, self.saldo2-self.mov1.importe)

    def test_desaparece_cta_salida_y_aparece_otra_cta_de_entrada_con_nuevo_importe(self):
        """ Suma importe viejo a cta_salida retirada
            Suma importe nuevo a cta_entrada agregada """
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.cta_salida = None
        self.mov2.importe = 675
        self.mov2.save()
        self.refresh_ctas()

        self.assertEqual(self.cuenta2.saldo, self.saldo2+self.mov2.importe)
        self.assertEqual(self.cuenta1.saldo, self.saldo1+self.imp2)


class TestModelMovimientoConCuentaAcumulativaModificar(TestModelMovimientoModificar):

    def setUp(self):
        super().setUp()
        self.mov4 = Movimiento.crear(
            'traspaso salida acum', 200, self.cuenta2, self.cuenta1)

        self.cuenta1 = dividir_en_dos_subcuentas(self.cuenta1)
        for mov in (self.mov1, self.mov2, self.mov3, self.mov4):
            mov.refresh_from_db()

    def test_no_puede_modificarse_importe_de_movimiento_con_cta_entrada_acumulativa(self):
        self.mov1.importe = 300
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov1.full_clean()

    def test_no_puede_modificarse_importe_de_movimiento_con_cta_salida_acumulativa(self):
        self.mov2.importe = 300
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov2.full_clean()

    def test_no_puede_modificarse_importe_de_mov_de_traspaso_con_una_cuenta_acumulativa(self):
        self.mov3.importe = 500
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov3.full_clean()

        self.mov4.importe = 500
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov4.full_clean()

    def test_no_puede_modificarse_importe_de_mov_de_traspaso_con_ambas_cuentas_acumulativa(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )

        self.mov3.importe = 600
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CAMBIO_IMPORTE_CON_CUENTA_ACUMULATIVA):
            self.mov3.full_clean()

    def test_no_puede_retirarse_cta_entrada_de_movimiento_si_es_acumulativa(self):
        self.mov1.cta_entrada = self.cuenta2
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov1.full_clean()

    def test_no_puede_retirarse_cta_salida_de_movimiento_si_es_acumulativa(self):
        self.mov2.cta_salida = self.cuenta2
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov2.full_clean()

    def test_no_puede_retirarse_cuenta_de_traspaso_si_es_acumulativa(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3')

        self.mov3.cta_entrada = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov3.full_clean()

        self.mov4.cta_salida = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov4.full_clean()

    def test_no_puede_retirarse_cuenta_de_traspaso_si_ambas_son_acumulativas(self):
        cuenta3 = Cuenta.crear('cuenta3', 'c3')
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )

        self.mov3.cta_entrada = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov3.full_clean()

        self.mov4.cta_salida = cuenta3
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_RETIRADA):
            self.mov4.full_clean()

    def test_no_puede_agregarse_cta_entrada_acumulativa_a_movimiento(self):
        mov1 = Movimiento.crear('entrada', 100, self.cuenta2)
        mov2 = Movimiento.crear('salida', 100, None, self.cuenta2)

        mov1.cta_entrada = self.cuenta1
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_AGREGADA):
            mov1.full_clean()

        mov2.cta_entrada = self.cuenta1
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_AGREGADA):
            mov2.full_clean()

    def test_puede_agregarse_contracuenta_interactiva_a_entrada_con_cta_acumulativa(self):
        self.mov1.cta_salida = self.cuenta2
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.cta_salida, self.cuenta2)

    def test_puede_agregarse_contracuenta_interactiva_a_salida_con_cta_acumulativa(self):
        self.mov2.cta_entrada = self.cuenta2
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(self.mov2.cta_entrada, self.cuenta2)

    def test_puede_modificarse_cta_interactiva_en_movimiento_con_cta_entrada_acumulativa(self):
        self.mov3.cta_salida = self.cuenta2
        self.mov3.full_clean()
        self.mov3.save()
        self.assertEqual(self.mov3.cta_salida, self.cuenta2)

    def test_puede_modificarse_cta_interactiva_en_movimiento_con_cta_salida_acumulativa(self):
        self.mov4.cta_entrada = self.cuenta2
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(self.mov4.cta_entrada, self.cuenta2)

    def test_puede_retirarse_cta_interactiva_en_movimiento_con_cta_entrada_acumulativa(self):
        self.mov3.cta_salida = None
        self.mov3.full_clean()
        self.mov3.save()
        self.assertIsNone(self.mov3.cta_salida)

    def test_puede_retirarse_cta_interactiva_en_movimiento_con_cta_salida_acumulativa(self):
        self.mov4.cta_entrada = None
        self.mov4.full_clean()
        self.mov4.save()
        self.assertIsNone(self.mov4.cta_entrada)

    def test_no_puede_agregarse_cta_salida_acumulativa_a_movimiento(self):
        mov1 = Movimiento.crear('entrada', 100, self.cuenta2)
        mov2 = Movimiento.crear('salida', 100, None, self.cuenta2)

        mov1.cta_salida = self.cuenta1
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_AGREGADA):
            mov1.full_clean()

        mov2.cta_salida = self.cuenta1
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                errors.CUENTA_ACUMULATIVA_AGREGADA):
            mov2.full_clean()

    def test_no_puede_eliminarse_movimiento_con_cuenta_acumulativa(self):
        with self.assertRaisesMessage(
            errors.ErrorCuentaEsAcumulativa,
            errors.MOVIMIENTO_CON_CA_ELIMINADO
        ):
            self.mov1.delete()

    def test_puede_modificarse_concepto_en_movimiento_de_entrada_con_cuenta_acumulativa(self):
        self.mov1.concepto = 'entrada cambiada'
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.concepto, 'entrada cambiada')

    def test_puede_modificarse_concepto_en_movimiento_de_salida_con_cuenta_acumulativa(self):
        self.mov2.concepto = 'salida cambiada'
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(
            self.mov2.concepto, 'salida cambiada')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_entrada(self):
        self.mov3.concepto = 'entrada cambiada en traspaso'
        self.mov3.full_clean()
        self.mov3.save()
        self.assertEqual(
            self.mov3.concepto, 'entrada cambiada en traspaso')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_salida(self):
        self.mov4.concepto = 'salida cambiada en traspaso'
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(
            self.mov4.concepto, 'salida cambiada en traspaso')

    def test_puede_modificarse_concepto_en_movimiento_de_traspaso_con_ambas_cuentas_acumulativas(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )
        self.mov4.concepto = 'concepto cambiado en traspaso'
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(
            self.mov4.concepto, 'concepto cambiado en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_entrada_con_cuenta_acumulativa(self):
        self.mov1.detalle = 'entrada cambiada'
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.detalle, 'entrada cambiada')

    def test_puede_modificarse_detalle_en_movimiento_de_salida_con_cuenta_acumulativa(self):
        self.mov2.detalle = 'salida cambiada'
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(
            self.mov2.detalle, 'salida cambiada')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_entrada(self):
        self.mov3.detalle = 'entrada cambiada en traspaso'
        self.mov3.full_clean()
        self.mov3.save()
        self.assertEqual(
            self.mov3.detalle, 'entrada cambiada en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_cuenta_acumulativa_en_salida(self):
        self.mov4.detalle = 'salida cambiada en traspaso'
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(
            self.mov4.detalle, 'salida cambiada en traspaso')

    def test_puede_modificarse_detalle_en_movimiento_de_traspaso_con_ambas_cuentas_acumulativas(self):
        self.cuenta2.dividir_entre(
            ['cuenta2 subcuenta 1', 'c2s1', 100],
            ['cuenta2 subcuenta2', 'c2s2']
        )
        self.mov4.detalle = 'detalle cambiado en traspaso'
        self.mov4.full_clean()
        self.mov4.save()
        self.assertEqual(
            self.mov4.detalle, 'detalle cambiado en traspaso')

    def test_puede_modificarse_fecha_en_movimiento_con_cta_entrada_acumulativa_si_nueva_fecha_es_anterior_a_conversion(self):
        self.mov1.fecha = date(2020, 1, 5)
        self.mov1.full_clean()
        self.mov1.save()
        self.assertEqual(self.mov1.fecha, date(2020, 1, 5))

    def test_puede_modificarse_fecha_en_movimiento_con_cta_salida_acumulativa_si_nueva_fecha_es_anterior_a_conversion(self):
        self.mov2.fecha = date(2020, 1, 5)
        self.mov2.full_clean()
        self.mov2.save()
        self.assertEqual(self.mov2.fecha, date(2020, 1, 5))

    def test_no_puede_asignarse_fecha_posterior_a_conversion_en_mov_con_cta_entrada_acumulativa(self):
        self.mov1.fecha = date.today() + timedelta(days=2)
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                f'{errors.FECHA_POSTERIOR_A_CONVERSION}{date.today()}'
        ):
            self.mov1.full_clean()

    def test_no_puede_asignarse_fecha_posterior_a_conversion_en_mov_con_cta_salida_acumulativa(self):
        self.mov2.fecha = date.today() + timedelta(days=2)
        with self.assertRaisesMessage(
                errors.ErrorCuentaEsAcumulativa,
                f'{errors.FECHA_POSTERIOR_A_CONVERSION}{date.today()}'
        ):
            self.mov2.full_clean()


class TestModelMovimientoPropiedadSentido(TestModelMovimiento):

    def test_devuelve_s_si_movimiento_tiene_solo_cuenta_de_salida(self):
        mov = Movimiento.crear(
            concepto='Pago en efectivo',
            importe=100,
            cta_salida=self.cuenta1,
        )
        self.assertEqual(mov.sentido, 's')

    def test_devuelve_e_si_movimiento_tiene_solo_cuenta_de_entrada(self):
        mov = Movimiento.crear(
            concepto='Pago en efectivo',
            importe=100,
            cta_entrada=self.cuenta1,
        )
        self.assertEqual(mov.sentido, 'e')

    def test_devuelve_t_si_novimiento_tiene_cuenta_de_entrada_y_salida(self):
        cuenta2 = Cuenta.crear("Banco", "bco")
        mov = Movimiento.crear(
            concepto='Pago a cuenta',
            importe=143,
            cta_entrada=cuenta2,
            cta_salida=self.cuenta1,
        )
        self.assertEqual(mov.sentido, 't')


class TestModelMovimientoPropiedadImporte(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.mov = Movimiento(
            concepto='Movimiento con importe',
            _importe=100,
            cta_entrada=self.cuenta1
        )
        self.mov.full_clean()
        self.mov.save()

    def test_devuelve_importe_del_movimiento(self):
        self.assertEqual(self.mov.importe, self.mov._importe)

    def test_asigna_valor_a_campo__importe(self):
        self.mov.importe = 300
        self.assertEqual(self.mov._importe, 300)

    def test_redondea_importe(self):
        self.mov.importe = 300.462
        self.assertEqual(self.mov._importe, 300.46)

    def test_funciona_con_strings(self):
        self.mov.importe = '200'
        self.assertEqual(self.mov._importe, 200)

    def test_redondea_strings(self):
        self.mov.importe = '222.2222'
        self.assertEqual(self.mov._importe, 222.22)


class TestModelMovimientoPropiedadesEmisorReceptor(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.titular2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta2 = Cuenta.crear(
            nombre='Cuenta titular 2', slug='ct2', titular=self.titular2)
        self.mov1 = Movimiento.crear(
            'Traspaso', 100, self.cuenta1, self.cuenta2, esgratis=True)

    def test_emisor_devuelve_titular_de_cuenta_de_salida_del_movimiento(self):
        self.assertEqual(self.mov1.emisor, self.titular2)

    def test_emisor_devuelve_none_si_movimiento_no_tiene_cuenta_de_salida(self):
        mov = Movimiento.crear('Entrada', 100, self.cuenta1)
        self.assertIsNone(mov.emisor)

    def test_receptor_devuelve_titular_de_cuenta_de_entrada_del_movimiento(self):
        self.assertEqual(self.mov1.receptor, self.titular1)

    def test_receptor_devuelve_none_si_movimiento_no_tiene_cuenta_de_entrada(self):
        mov = Movimiento.crear('Entrada', 100, cta_salida=self.cuenta1)
        self.assertIsNone(mov.receptor)


class TestModelMovimientoMetodoStr(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.cta2 = Cuenta.crear(
            nombre='Banco', slug='B', titular=self.titular1)

    def test_muestra_movimiento_con_cuenta_de_entrada_y_salida(self):
        mov1 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Retiro de efectivo',
            importe='250.2',
            cta_entrada=self.cuenta1,
            cta_salida=self.cta2
        )
        self.assertEqual(
            str(mov1),
            '2021-03-22 Retiro de efectivo: 250.2 +cuenta titular 1 -banco'
        )

    def test_muestra_movimiento_sin_cuenta_de_salida(self):
        mov2 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Carga de saldo',
            importe='500',
            cta_entrada=self.cuenta1,
        )
        self.assertEqual(
            str(mov2),
            '2021-03-22 Carga de saldo: 500 +cuenta titular 1'
        )

    def test_muestra_movimiento_sin_cuenta_de_entrada(self):
        mov3 = Movimiento(
            fecha=date(2021, 3, 22),
            concepto='Transferencia',
            importe='300.35',
            cta_salida=self.cta2
        )
        self.assertEqual(
            str(mov3),
            '2021-03-22 Transferencia: 300.35 -banco'
        )


class TestModelMovimientoMetodoTieneCuentaAcumulativa(TestModelMovimiento):

    def test_devuelve_true_si_mov_tiene_una_cuenta_acumulativa(self):
        cuenta2 = Cuenta.crear('cuenta2', 'c2')
        mov = Movimiento.crear(
            'traspaso', 100, cta_entrada=self.cuenta1, cta_salida=cuenta2)
        self.cuenta1.dividir_entre(['subc1', 'sc1', 60], ['subc2', 'sc2'])
        mov.refresh_from_db()

        self.assertTrue(mov.tiene_cuenta_acumulativa())

    def test_devuelve_false_si_mov_no_tiene_cuenta_acumulativa(self):
        cuenta2 = Cuenta.crear('cuenta2', 'c2')
        mov = Movimiento.crear(
            'traspaso', 100, cta_entrada=self.cuenta1, cta_salida=cuenta2)
        mov.refresh_from_db()
        self.assertFalse(mov.tiene_cuenta_acumulativa())


class TestModelMovimientoMetodoEsPrestamo(TestModelMovimientoModificar):

    def test_devuelve_true_si_mov_es_traspaso_entre_cuentas_de_distinto_titular(self):
        mov = Movimiento.crear(
            'traspaso', 100, cta_entrada=self.cuenta1, cta_salida=self.cuenta3)
        self.assertTrue(mov.es_prestamo())

    def test_devuelve_false_si_mov_no_es_traspaso(self):
        self.assertFalse(self.mov1.es_prestamo())

    def test_devuelve_false_si_cuentas_pertenecen_al_mismo_titular(self):
        self.assertFalse(self.mov3.es_prestamo())

    def test_devuelve_false_si_mov_es_gratis(self):
        mov = Movimiento.crear(
            concepto='traspaso',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta3,
        )
        self.assertFalse(mov.es_prestamo(esgratis=True))


class TestModelMovimientoMetodoGenerarCuentasCredito(TestModelMovimientoEntreTitulares):

    def test_crea_dos_cuentas_credito(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta2, esgratis=True)
        movimiento._generar_cuentas_credito(Cuenta)
        self.assertEqual(Cuenta.cantidad(), 4)
        cc1 = list(Cuenta.todes())[-2]
        cc2 = list(Cuenta.todes())[-1]
        self.assertEqual(cc1.slug, '_tit1-tit2')
        self.assertEqual(cc2.slug, '_tit2-tit1')

    def test_no_funciona_en_movimiento_que_no_sea_entre_titulares(self):
        self.cuenta3 = Cuenta.crear('Cuenta 3', 'c3', titular=self.titular1)
        movimiento = Movimiento.crear('Traspaso', 10, self.cuenta3, self.cuenta1)
        with self.assertRaises(errors.ErrorMovimientoNoPrestamo):
            movimiento._generar_cuentas_credito(Cuenta)

    def test_no_funciona_en_movimiento_que_no_sea_de_traspaso(self):
        movimiento = Movimiento.crear('Traspaso', 10, self.cuenta1)
        with self.assertRaises(errors.ErrorMovimientoNoPrestamo):
            movimiento._generar_cuentas_credito(Cuenta)

    def test_guarda_cuenta_credito_acreedor_como_contracuenta_de_cuenta_credito_deudor(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta2, esgratis=True)
        cc2, cc1 = movimiento._generar_cuentas_credito(Cuenta)
        self.assertEqual(cc1._contracuenta, cc2)

    def test_guarda_cuenta_credito_deudor_como_contracuenta_de_cuenta_credito_acreedor(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta2, esgratis=True)
        cc2, cc1 = movimiento._generar_cuentas_credito(Cuenta)
        self.assertEqual(cc2._cuentacontra, cc1)


class TestModelMovimientoMetodoEliminarContramovimiento(TestModelMovimientoModificar):

    def test_elimina_contramovimiento(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        id_contramovimiento = movimiento.id_contramov

        movimiento._eliminar_contramovimiento()

        with self.assertRaises(Movimiento.DoesNotExist):
            Movimiento.tomar(id=id_contramovimiento)

    def test_elimina_id_contramov(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        movimiento._eliminar_contramovimiento()
        self.assertIsNone(movimiento.id_contramov)


class TestModelMovimientoMetodoRegenerarContramovimiento(TestModelMovimientoModificar):

    @patch.object(Movimiento, '_eliminar_contramovimiento', autospec=True)
    def test_elimina_contramovimiento(self, mock_eliminar_contramovimiento):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        movimiento._regenerar_contramovimiento()

        mock_eliminar_contramovimiento.assert_called_once_with(movimiento)

    def test_regenera_contramovimiento(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)

        with patch.object(
                Movimiento, '_crear_movimiento_credito', autospec=True
        ) as mock_crear_movimiento_credito:

            movimiento._regenerar_contramovimiento()

            mock_crear_movimiento_credito.assert_called_once_with(movimiento)

    def test_actualiza_id_contramovimiento(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        movimiento._regenerar_contramovimiento()
        contramov = Movimiento.ultime()
        self.assertEqual(movimiento.id_contramov, contramov.id)


class TestModelMovimientoMetodoCambiaCampo(TestModelMovimientoModificar):

    def setUp(self):
        super().setUp()
        self.mov1.importe = 156

    def test_devuelve_true_si_hay_cambio_en_alguno_de_los_campos_dados(self):
        self.assertTrue(self.mov1._cambia_campo('importe', 'fecha'))

    def test_devuelve_false_si_no_hay_cambio_en_ninguno_de_los_campos_dados(self):
        self.assertFalse(self.mov1._cambia_campo('concepto', 'fecha'))
