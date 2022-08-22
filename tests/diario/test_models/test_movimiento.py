from datetime import date, timedelta
from unittest.mock import patch, call

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, CuentaInteractiva, CuentaAcumulativa, \
    Movimiento, Titular, Saldo
from utils import errors
from utils.helpers_tests import dividir_en_dos_subcuentas


class TestModelMovimiento(TestCase):

    def setUp(self):
        self.cuenta1 = Cuenta.crear(
            nombre='Cuenta titular 1',
            slug='ct1',
            fecha_creacion=date(2011, 1, 1)
        )


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
            nombre='Cuenta 2',
            slug='ct2',
            fecha_creacion=date(2011, 11, 12)
        )
        self.mov1 = Movimiento.crear(
            fecha=date(2011, 11, 12),
            concepto='Carga de saldo',
            importe=140,
            cta_entrada=self.cuenta1
        )
        self.mov2 = Movimiento.crear(
            fecha=date(2011, 11, 12),
            concepto='Transferencia a otra cuenta',
            importe=50,
            cta_salida=self.cuenta2
        )

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

    def test_movimiento_se_guarda_como_no_automatico_por_defecto(self):
        mov = Movimiento.crear('Pago', '200', cta_entrada=self.cuenta1)
        self.assertFalse(mov.es_automatico)

    def test_suma_importe_a_cta_entrada(self):
        self.assertEqual(self.cuenta1.saldo, 140)

    def test_resta_importe_de_cta_salida(self):
        self.assertEqual(self.cuenta2.saldo, -50)

    def test_puede_traspasar_saldo_de_una_cuenta_a_otra(self):
        Movimiento.crear(
            concepto='Depósito',
            importe=60,
            cta_entrada=self.cuenta2,
            cta_salida=self.cuenta1
        )
        self.assertEqual(self.cuenta2.saldo, -50+60)
        self.assertEqual(self.cuenta1.saldo, 140-60)

    @patch('diario.models.movimiento.Saldo.generar')
    def test_mov_entrada_llama_a_generar_saldo_con_salida_False(self, mock_generar):
        mov = Movimiento.crear(
            'Nuevo mov', 20, self.cuenta1, fecha=date(2011, 11, 15))
        mock_generar.assert_called_once_with(mov, salida=False)

    @patch('diario.models.movimiento.Saldo.generar')
    def test_mov_salida_llama_a_generar_saldo_con_salida_True(self, mock_generar):
        mov = Movimiento.crear(
            'Nuevo mov', 20, None, self.cuenta1, fecha=date(2011, 11, 15))
        mock_generar.assert_called_once_with(mov, salida=True)

    @patch('diario.models.movimiento.Saldo.generar')
    def test_mov_traspaso_llama_a_generar_saldo_con_salida_false_para_cta_entrada_y_salida_True_para_cta_salida(self, mock_generar):
        mov = Movimiento.crear(
            'Nuevo mov', 20, self.cuenta1, self.cuenta2, fecha=date(2011, 11, 15))

        self.assertEqual(
            mock_generar.call_args_list,
            [call(mov, salida=False), call(mov, salida=True)]
        )

    def test_integrativo_genera_saldo_para_cta_entrada(self):
        mov = Movimiento.crear(
            'Nuevo mov', 20, self.cuenta1, fecha=date(2011, 11, 15))

        saldo = Saldo.objects.get(cuenta=self.cuenta1, movimiento=mov)
        self.assertEqual(saldo.cuenta.pk, self.cuenta1.pk)
        self.assertEqual(saldo.importe, 140+20)
        self.assertEqual(saldo.movimiento, mov)

    def test_integrativo_genera_saldo_para_cta_salida(self):
        mov = Movimiento.crear(
            'Nuevo mov', 20, None, self.cuenta1, fecha=date(2011, 11, 15))
        saldo = Saldo.objects.get(cuenta=self.cuenta1, movimiento=mov)
        self.assertEqual(saldo.cuenta.pk, self.cuenta1.pk)
        self.assertEqual(saldo.importe, 140-20)
        self.assertEqual(saldo.movimiento, mov)

    def test_integrativo_crear_movimiento_en_fecha_antigua_modifica_saldos_de_fechas_posteriores(self):
        Movimiento.crear(
            'Movimiento anterior', 30, self.cuenta1, fecha=date(2011, 11, 11))

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=self.mov1).importe,
            170
        )


class TestModelMovimientoCrearEntreTitulares(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.titular1 = Titular.tomar(titname='default')
        self.titular2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta2 = Cuenta.crear(
            'Cuenta titular 2', 'ct2', titular=self.titular2)


class TestModelMovimientoCrearEntreTitularesPrimero(
        TestModelMovimientoCrearEntreTitulares):

    @patch('diario.models.Movimiento._gestionar_transferencia', autospec=True)
    def test_movimiento_entre_titulares_gestiona_trasferencia(self, mock_gestionar_transferencia):
        mov = Movimiento(
            concepto='Préstamo',
            importe=10,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2
        )
        mov.save()
        mock_gestionar_transferencia.assert_called_once_with(mov)

    @patch('diario.models.Movimiento._gestionar_transferencia')
    def test_movimiento_no_entre_titulares_no_gestiona_transferencia(self, mock_gestionar_transferencia):
        cuenta3 = Cuenta.crear('cuenta 2 default', 'c2d')
        mov = Movimiento(
            concepto='Préstamo',
            importe=10,
            cta_entrada=self.cuenta1,
            cta_salida=cuenta3
        )
        mov.save()
        mock_gestionar_transferencia.assert_not_called()

    @patch('diario.models.Movimiento._gestionar_transferencia')
    def test_no_gestiona_transferencia_si_esgratis(self, mock_gestionar_transferencia):
        mov = Movimiento(
            concepto='Prestamo', importe=10,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2,
        )
        mov.esgratis = True
        mov.save()
        mock_gestionar_transferencia.assert_not_called()

    def test_integrativo_genera_contramovimiento(self):
        Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        self.assertEqual(Movimiento.cantidad(), 2)

        cuenta_deudora = Cuenta.tomar(slug='_default-tit2')
        cuenta_acreedora = Cuenta.tomar(slug='_tit2-default')
        mov_credito = Movimiento.tomar(concepto='Constitución de crédito')
        self.assertEqual(
            mov_credito.detalle,
            'de Titular 2 a Titular por defecto'
        )
        self.assertEqual(mov_credito.importe, 10)
        self.assertEqual(mov_credito.cta_entrada, cuenta_acreedora)
        self.assertEqual(mov_credito.cta_salida, cuenta_deudora)

    def test_integrativo_genera_cuenta_credito_y_subcuentas_y_movimiento(self):
        movimiento = Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        self.assertEqual(Cuenta.cantidad(), 4)
        self.assertEqual(Movimiento.cantidad(), 2)

        cuenta_deudora = Cuenta.tomar(slug='_default-tit2')
        cuenta_acreedora = Cuenta.tomar(slug='_tit2-default')
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

    def test_integrativo_no_genera_nada_si_esgratis(self):
        Movimiento.crear(
            'Prestamo', 10,
            cta_entrada=self.cuenta1, cta_salida=self.cuenta2,
            esgratis=True
        )
        self.assertEqual(Cuenta.cantidad(), 2)
        self.assertEqual(Movimiento.cantidad(), 1)


class TestModelMovimientoClean(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.titular1 = Titular.tomar(titname='default')
        self.titular2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta2 = Cuenta.crear(
            nombre='Cuenta titular 2', slug='ct2', titular=self.titular2)

    def generar_cuentas_credito(self):
        cta_otro_tit = Cuenta.crear(
            'cuenta otro titular', 'cot', titular=self.titular2)
        mov = Movimiento.crear('Préstamo', 100, cta_otro_tit, self.cuenta1)
        return mov.recuperar_cuentas_credito()

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

    def test_movimiento_de_entrada_no_admite_cuenta_credito(self):
        cc12, cc21 = self.generar_cuentas_credito()
        mov_no_e = Movimiento(
            concepto='Movimiento prohibido',
            importe=50,
            cta_entrada=cc21,
        )
        with self.assertRaisesMessage(
            ValidationError,
            'No se permite cuenta crédito en movimiento de entrada o salida'
        ):
            mov_no_e.full_clean()

    def test_movimiento_de_salida_no_admite_cuenta_credito(self):
        cc12, cc21 = self.generar_cuentas_credito()
        mov_no_s = Movimiento(
            concepto='También prohibido',
            importe=50,
            cta_salida=cc12
        )

        with self.assertRaisesMessage(
            ValidationError,
            'No se permite cuenta crédito en movimiento de entrada o salida'
        ):
            mov_no_s.full_clean()

    def test_cuenta_credito_no_puede_ser_cta_entrada_contra_cta_salida_normal(self):
        cc12, cc21 = self.generar_cuentas_credito()
        mov_no = Movimiento(
            concepto='Movimiento prohibido',
            importe=50,
            cta_entrada=cc21,
            cta_salida=self.cuenta1
        )

        with self.assertRaisesMessage(
            ValidationError,
            'No se permite traspaso entre cuenta crédito y cuenta normal'
        ):
            mov_no.full_clean()

    def test_cuenta_credito_no_puede_ser_cta_salida_contra_cta_entrada_normal(self):
        cc12, cc21 = self.generar_cuentas_credito()
        mov_no = Movimiento(
            concepto='Movimiento prohibido',
            importe=50,
            cta_entrada=self.cuenta1,
            cta_salida=cc12
        )

        with self.assertRaisesMessage(
                ValidationError,
                'No se permite traspaso entre cuenta crédito y cuenta normal'
        ):
            mov_no.full_clean()

    def test_cuenta_credito_solo_puede_moverse_contra_su_contracuenta(self):
        cc12, cc21 = self.generar_cuentas_credito()
        titular3 = Titular.crear(nombre='Titular 3', titname='tit3')
        cuenta3 = Cuenta.crear(
            nombre='Cuenta titular 3', slug='ct3', titular=titular3)
        movimiento2 = Movimiento.crear(
            'Otro préstamo', 70, self.cuenta2, cuenta3)
        cc32, cc23 = movimiento2.recuperar_cuentas_credito()
        mov_no = Movimiento(
            concepto='Movimiento prohibido',
            importe=50,
            cta_entrada=cc21,
            cta_salida=cc32
        )

        with self.assertRaisesMessage(
            ValidationError,
            '"préstamo entre tit3 y tit2" no es la contrapartida '
            'de "préstamo entre tit2 y default"'
        ):
            mov_no.full_clean()


class TestModelMovimientoSave(TestModelMovimiento):
    """ Saldos después de setUp:
        self.cuenta1: 125.0-35+50 = 140
        self.cuenta2: = -50
    """

    def setUp(self):
        super().setUp()
        self.titular2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta2 = Cuenta.crear(
            'cuenta 2', 'c2',
            fecha_creacion=date(2020, 1, 5)
        )
        self.cuenta3 = Cuenta.crear(
            'Cuenta otro titular', 'ct2',
            titular=self.titular2,
            fecha_creacion=date(2020, 1, 5)
        )
        self.mov1 = Movimiento.crear(
            'entrada', 125, self.cuenta1, fecha=date(2021, 1, 5))
        self.mov2 = Movimiento.crear(
            'salida', 35, None, self.cuenta1, fecha=date(2021, 1, 10))
        self.mov3 = Movimiento.crear(
            'traspaso', 50, self.cuenta1, self.cuenta2, fecha=date(2021, 1, 11)
        )

    def refresh_ctas(self, *args):
        self.cuenta1.refresh_from_db()
        self.cuenta2.refresh_from_db()
        self.cuenta3.refresh_from_db()
        for arg in args:
            arg.refresh_from_db()


class TestModelMovimientoRefreshFromDb(TestModelMovimientoSave):

    def test_mantiene_tipos_especificos_de_cuentas_de_entrada_y_salida(self):
        dividir_en_dos_subcuentas(self.cuenta1)
        self.mov3.refresh_from_db()
        self.assertEqual(type(self.mov3.cta_salida), CuentaInteractiva)
        self.assertEqual(type(self.mov3.cta_entrada), CuentaAcumulativa)


class TestModelMovimientoEliminar(TestModelMovimientoSave):

    def test_eliminar_movimiento_resta_de_saldo_cta_entrada_y_suma_a_saldo_cta_salida(self):

        self.mov1.delete()

        self.assertEqual(self.cuenta1.saldo, 140-125)

        self.mov3.delete()

        self.assertEqual(self.cuenta2.saldo, -50+50)
        self.assertEqual(self.cuenta1.saldo, 15-50)

    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_eliminar_movimiento_elimina_saldo_cta_entrada_al_momento_del_movimiento(self, mock_eliminar):
        saldo = Saldo.tomar(cuenta=self.cuenta1, movimiento=self.mov1)
        self.mov1.delete()
        mock_eliminar.assert_called_once_with(saldo)

    def test_integrativo_eliminar_movimiento_elimina_saldo_cta_entrada_al_momento_del_movimiento(self):
        mov = self.mov1
        self.mov1.delete()
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=mov.cta_entrada, movimiento=mov)

    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_eliminar_movimiento_elimina_saldo_cta_salida_al_momento_del_movimiento(self, mock_eliminar):
        saldo = Saldo.tomar(cuenta=self.cuenta1, movimiento=self.mov2)
        self.mov2.delete()
        mock_eliminar.assert_called_once_with(saldo)

    def test_integrativo_eliminar_movimiento_elimina_saldo_cta_salida_al_momento_del_movimiento(self):
        mov = self.mov1
        self.mov1.delete()
        with self.assertRaises(Saldo.DoesNotExist):
            Saldo.objects.get(cuenta=mov.cta_salida, movimiento=mov)

    def test_eliminar_movimiento_resta_importe_de_saldos_posteriores_de_cta_entrada(self):
        self.mov1.delete()
        self.assertEqual(
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3).importe,
            140-125
        )

    def test_eliminar_movimiento_suma_importe_a_saldos_posteriores_de_cta_salida(self):
        self.assertEqual(
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3).importe,
            140
        )
        self.mov2.delete()
        self.assertEqual(
            Saldo.objects.get(cuenta=self.cuenta1, movimiento=self.mov3).importe,
            140+35
        )


class TestModelMovimientoEliminarConContramovimiento(TestModelMovimientoSave):

    def setUp(self):
        super().setUp()
        self.movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        self.contramov = Movimiento.tomar(id=self.movimiento.id_contramov)

    @patch.object(Movimiento, '_eliminar_contramovimiento', autospec=True)
    def test_elimina_contramovimiento(
            self, mock_eliminar_contramovimiento):
        self.movimiento.delete()
        mock_eliminar_contramovimiento.assert_called_once_with(self.movimiento)

    def test_repone_saldo_de_cuentas_credito(self):
        cta_deudora = self.contramov.cta_salida
        cta_acreedora = self.contramov.cta_entrada

        self.movimiento.delete()

        self.assertEqual(cta_deudora.saldo, 0)
        self.assertEqual(cta_acreedora.saldo, 0)

    def test_no_se_permite_eliminar_contramovimientos(self):
        with self.assertRaisesMessage(
                ValidationError,
                'No se puede eliminar movimiento automático'):
            self.contramov.delete()

    def test_se_permite_eliminar_contramovimiento_con_force_true(self):
        try:
            self.contramov.delete(force=True)
        except errors.ErrorMovimientoAutomatico:
            raise AssertionError(
                'No se eliminó contramovimiento a pesar de force=True')


class TestModelMovimientoDeSubcuentaEliminar(TestModelMovimientoSave):

    def setUp(self):
        super().setUp()
        self.cuenta1 = dividir_en_dos_subcuentas(
            self.cuenta1,
            saldo=25,
            fecha=date(2021, 1, 11)
        )
        self.subc11 = Cuenta.tomar(slug='sc1')
        self.subc12 = Cuenta.tomar(slug='sc2')
        self.fecha = date(2021, 1, 15)

    def test_si_se_elimina_mov_con_subcuenta_como_cta_entrada_se_resta_importe_del_mov_de_saldo_de_cta_madre_en_fecha(self):
        mov = Movimiento.crear('mov subc', 45, self.subc11, fecha=self.fecha)
        saldo = Saldo.tomar(cuenta=self.cuenta1, movimiento=mov).importe
        mov.delete()

        with self.assertRaises(Saldo.DoesNotExist):
            self.subc11.saldo_set.get(movimiento=mov)

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov).importe,
            saldo-45
        )

    def test_si_se_elimina_mov_con_subcuenta_como_cta_salida_se_suma_importe_del_mov_a_saldo_de_cta_madre_en_fecha(self):
        mov = Movimiento.crear('mov subc', 45, None, self.subc11, fecha=self.fecha)
        saldo = Saldo.tomar(cuenta=self.cuenta1, movimiento=mov).importe
        mov.delete()

        with self.assertRaises(Saldo.DoesNotExist):
            self.subc11.saldo_set.get(movimiento=mov)

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, movimiento=mov).importe,
            saldo+45
        )


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
        self.titular1 = Titular.tomar(titname='default')
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
        self.titular1 = Titular.tomar(titname='default')
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
            '2021-03-22 Retiro de efectivo: 250.20 +cuenta titular 1 -banco'
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
            '2021-03-22 Carga de saldo: 500.00 +cuenta titular 1'
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


class TestModelMovimientoMetodoSaldoCE(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.mov1 = Movimiento.crear('mov1', 100, self.cuenta1)
        self.mov2 = Movimiento.crear('mov2', 200, None, self.cuenta1)

    def test_devuelve_saldo_de_cta_entrada_al_momento_del_movimiento(self):
        self.assertEqual(
            self.mov1.saldo_ce(),
            self.mov1.cta_entrada.saldo_set.get(movimiento=self.mov1)
        )

    def test_si_no_hay_cta_entrada_tira_error(self):
        with self.assertRaisesMessage(
            AttributeError,
            'Movimiento "mov2" no tiene cuenta de entrada'
        ):
            self.mov2.saldo_ce()


class TestModelMovimientoMetodoSaldoCS(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.mov1 = Movimiento.crear('mov1', 100, self.cuenta1)
        self.mov2 = Movimiento.crear('mov2', 200, None, self.cuenta1)

    def test_devuelve_saldo_de_cta_entrada_al_momento_del_movimiento(self):
        self.assertEqual(
            self.mov2.saldo_cs(),
            self.mov2.cta_salida.saldo_set.get(movimiento=self.mov2)
        )

    def test_si_no_hay_cta_entrada_tira_error(self):
        with self.assertRaisesMessage(
            AttributeError,
            'Movimiento "mov1" no tiene cuenta de salida'
        ):
            self.mov1.saldo_cs()


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


class TestModelMovimientoMetodoEsPrestamo(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.tit1 = Titular.tomar(titname='default')
        self.tit2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta2 = Cuenta.crear('cuenta tit 2', 'ct2', titular=self.tit2)
        self.cuenta3 = Cuenta.crear('cuenta 2 tit 2', 'c2t2', titular=self.tit2)

    def test_devuelve_true_si_mov_es_traspaso_entre_cuentas_de_distinto_titular(self):
        mov = Movimiento.crear(
            'traspaso', 100, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        self.assertTrue(mov.es_prestamo_o_devolucion())

    def test_devuelve_false_si_mov_no_es_traspaso(self):
        mov = Movimiento.crear('entrada', 100, self.cuenta1)
        self.assertFalse(mov.es_prestamo_o_devolucion())

    def test_devuelve_false_si_cuentas_pertenecen_al_mismo_titular(self):
        mov = Movimiento.crear('traspaso', 100, self.cuenta2, self.cuenta3)
        self.assertFalse(mov.es_prestamo_o_devolucion())

    def test_devuelve_false_si_mov_es_gratis(self):
        mov = Movimiento.crear(
            concepto='traspaso',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta3,
            esgratis=True
        )
        self.assertFalse(mov.es_prestamo_o_devolucion())


class TestModelMovimientoMetodoEsAnteriorA(TestModelMovimiento):

    def test_True_si_fecha_es_anterior_a_fecha_de_otro_False_si_es_posterior(self):
        m1 = Movimiento.crear('m1', 100, self.cuenta1, fecha=date(2012, 1, 5))
        m2 = Movimiento.crear('m2', 100, self.cuenta1, fecha=date(2012, 1, 3))

        self.assertTrue(m2.es_anterior_a(m1))
        self.assertFalse(m1.es_anterior_a(m2))

    def test_True_si_fecha_es_igual_y_orden_dia_es_menor_que_el_de_otro_False_si_es_mayor(self):
        m1 = Movimiento.crear('m1', 100, self.cuenta1, fecha=date(2012, 1, 5))
        m2 = Movimiento.crear('m2', 100, self.cuenta1, fecha=date(2012, 1, 5), orden_dia=0)
        m1.refresh_from_db(fields=['orden_dia'])

        self.assertTrue(m2.es_anterior_a(m1))
        self.assertFalse(m1.es_anterior_a(m2))


class TestModelMovimientoMetodoGenerarCuentasCredito(TestModelMovimientoCrearEntreTitulares):

    def test_crea_dos_cuentas_credito(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta2, esgratis=True)
        movimiento._generar_cuentas_credito()
        self.assertEqual(Cuenta.cantidad(), 4)
        cc1 = list(Cuenta.todes())[-2]
        cc2 = list(Cuenta.todes())[-1]
        self.assertEqual(cc1.slug, '_default-tit2')
        self.assertEqual(cc2.slug, '_tit2-default')

    def test_no_funciona_en_movimiento_que_no_sea_entre_titulares(self):
        self.cuenta3 = Cuenta.crear('Cuenta 3', 'c3', titular=self.titular1)
        movimiento = Movimiento.crear('Traspaso', 10, self.cuenta3, self.cuenta1)
        with self.assertRaises(errors.ErrorMovimientoNoPrestamo):
            movimiento._generar_cuentas_credito()

    def test_no_funciona_en_movimiento_que_no_sea_de_traspaso(self):
        movimiento = Movimiento.crear('Traspaso', 10, self.cuenta1)
        with self.assertRaises(errors.ErrorMovimientoNoPrestamo):
            movimiento._generar_cuentas_credito()

    def test_guarda_cuenta_credito_acreedor_como_contracuenta_de_cuenta_credito_deudor(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta2, esgratis=True)
        cc2, cc1 = movimiento._generar_cuentas_credito()
        self.assertEqual(cc1._contracuenta, cc2)

    def test_guarda_cuenta_credito_deudor_como_contracuenta_de_cuenta_credito_acreedor(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta1, self.cuenta2, esgratis=True)
        cc2, cc1 = movimiento._generar_cuentas_credito()
        self.assertEqual(cc2._cuentacontra, cc1)


class TestModelMovimientoMetodoEliminarContramovimiento(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.tit2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta2 = Cuenta.crear('Cuenta tit 2', 'ct2', titular=self.tit2)
        self.cuenta3 = Cuenta.crear('Cuenta 2 tit 2', 'c2t2', titular=self.tit2)

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

    def test_si_al_eliminar_contramovimiento_se_cancela_deuda_retira_titular_cta_entrada_de_acreedores_de_titular_cta_salida_y_viceversa(self):
        tit1 = Titular.tomar(titname='default')
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        movimiento._eliminar_contramovimiento()
        self.assertNotIn(tit1, self.tit2.acreedores.all())
        self.assertNotIn(self.tit2, tit1.deudores.all())


class TestModelMovimientoMetodoRegenerarContramovimiento(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        tit2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta2 = Cuenta.crear('Cuenta tit 2', 'ct2', titular=tit2)
        self.cuenta3 = Cuenta.crear('Cuenta 2 tit 2', 'c2t2', titular=tit2)

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


class TestModelMovimientoMetodoCambiaCampo(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.mov1 = Movimiento.crear('Movimiento', 100, self.cuenta1)
        self.mov1.importe = 156

    def test_devuelve_true_si_hay_cambio_en_alguno_de_los_campos_dados(self):
        self.assertTrue(self.mov1.cambia_campo('importe', 'fecha'))

    def test_devuelve_false_si_no_hay_cambio_en_ninguno_de_los_campos_dados(self):
        self.assertFalse(self.mov1.cambia_campo('concepto', 'fecha'))

    def test_acepta_un_movimiento_contra_el_cual_comparar(self):
        mov2 = Movimiento(concepto='Movimento', importe=156, cta_entrada=self.cuenta1)
        self.assertTrue(self.mov1.cambia_campo('concepto', contraparte=mov2))
        self.assertFalse(self.mov1.cambia_campo('importe', contraparte=mov2))


class TestModelMovimientoMetodoCrearMovimientoCredito(
    TestModelMovimientoCrearEntreTitulares):

    def setUp(self):
        super().setUp()
        self.mov = Movimiento(
            concepto='Prestamo',
            importe=10,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2
        )

    @patch('diario.models.Movimiento.recuperar_cuentas_credito', autospec=True)
    @patch('diario.models.Movimiento.crear')
    def test_intenta_recuperar_cuentas_credito(self, mock_crear, mock_recuperar_cuentas_credito):
        mock_recuperar_cuentas_credito.return_value = (
            Cuenta(nombre='mock1', slug='mock1'),
            Cuenta(nombre='mock2', slug='mock2')
        )
        self.mov._crear_movimiento_credito()
        mock_recuperar_cuentas_credito.assert_called_once_with(self.mov)

    @patch('diario.models.Movimiento._generar_cuentas_credito', autospec=True)
    @patch('diario.models.Movimiento.crear')
    def test_genera_cuentas_credito_si_no_existen(self, mock_crear, mock_generar_cuentas_credito):
        mock_generar_cuentas_credito.return_value = (
            Cuenta(nombre='mock1', slug='mock1'),
            Cuenta(nombre='mock2', slug='mock2')
        )
        self.mov._crear_movimiento_credito()
        mock_generar_cuentas_credito.assert_called_once_with(self.mov)

    @patch('diario.models.Movimiento._generar_cuentas_credito')
    def test_no_genera_cuentas_credito_si_existen(self, mock_generar_cuentas_credito):
        Cuenta.crear('Préstamo entre tit2 y default', '_tit2-default')
        Cuenta.crear('Preśtamo entre default y tit2', '_default-tit2')

        self.mov._crear_movimiento_credito()

        mock_generar_cuentas_credito.assert_not_called()

    def test_no_genera_cuentas_credito_en_movimiento_inverso_entre_titulares_con_credito_existente(self):
        Movimiento.crear('Préstamo', 10, self.cuenta2, self.cuenta1)

        with patch('diario.models.Movimiento._generar_cuentas_credito') \
                as mock_generar_cuentas_credito:
            self.mov._crear_movimiento_credito()
            mock_generar_cuentas_credito.assert_not_called()

    def test_resta_importe_de_cuenta_credito_en_movimiento_inverso_entre_titulares_con_credito_existente(self):
        Movimiento.crear('Préstamo', 14, self.cuenta2, self.cuenta1)

        self.mov._crear_movimiento_credito()

        self.assertEqual(Cuenta.tomar(slug='_default-tit2').saldo, 4)

    def test_suma_importe_a_cuenta_deuda_en_movimiento_inverso_entre_titulares_con_credito_existente(self):
        Movimiento.crear('Préstamo', 14, self.cuenta2, self.cuenta1)

        self.mov._crear_movimiento_credito()

        self.assertEqual(Cuenta.tomar(slug='_tit2-default').saldo, -4)

    @patch('diario.models.Movimiento._concepto_movimiento_credito')
    def test_determina_concepto_del_movimiento_de_credito_en_base_a_datos_de_las_cuentas_credito_creadas(self, mock_concepto_movimiento_credito):
        self.mov._crear_movimiento_credito()
        mock_concepto_movimiento_credito.assert_called_once_with(
            *self.mov.recuperar_cuentas_credito()
        )

    def test_integrativo_genera_cuentas_credito_si_no_existen(self):
        Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)

        self.assertEqual(Cuenta.cantidad(), 4)

        cc1 = Cuenta.todes()[2]
        cc2 = Cuenta.ultime()

        self.assertEqual(cc2.nombre, 'préstamo entre tit2 y default')
        self.assertEqual(cc2.slug, '_tit2-default')
        self.assertEqual(cc2.titular, self.titular2)
        self.assertEqual(cc1.nombre, 'préstamo entre default y tit2')
        self.assertEqual(cc1.slug, '_default-tit2')
        self.assertEqual(cc1.titular, self.titular1)

    @patch('diario.models.Movimiento.crear')
    @patch('diario.models.Movimiento._generar_cuentas_credito')
    def test_genera_contramovimiento(self, mock_generar_cuentas_credito, mock_crear):
        cd = Cuenta.crear('cuenta crédito deudora', 'ccd')
        ca = Cuenta.crear('cuenta crédito acreedora', 'cca')
        mock_generar_cuentas_credito.return_value = cd, ca

        self.mov._crear_movimiento_credito()

        mock_crear.assert_called_once_with(
            fecha=self.mov.fecha,
            concepto='Constitución de crédito',
            detalle='de Titular 2 a Titular por defecto',
            importe=10,
            cta_entrada=cd,
            cta_salida=ca,
            es_automatico=True,
            esgratis=True
        )

    def test_guarda_id_de_contramovimiento_en_movimiento(self):
        self.mov._crear_movimiento_credito()
        mov_credito = Movimiento.tomar(concepto='Constitución de crédito')
        self.assertEqual(self.mov.id_contramov, mov_credito.id)

    def test_movimiento_generado_se_marca_como_automatico(self):
        self.mov._crear_movimiento_credito()
        mov_credito = Movimiento.tomar(id=self.mov.id_contramov)
        self.assertTrue(mov_credito.es_automatico)


class TestModelMovimientoMetodoConceptoMovimientoCredito(TestCase):

    def setUp(self):
        self.cuenta_acreedora = Cuenta.crear('cuenta acreedora', 'ca')
        self.cuenta_deudora = Cuenta.crear('cuenta deudora', 'cd')
        self.mov = Movimiento()

    def test_si_cuenta_acreedora_tiene_saldo_positivo_devuelve_aumento_de_credito(self):
        Movimiento.crear('saldo ca', 100, self.cuenta_acreedora)
        self.assertEqual(
            self.mov._concepto_movimiento_credito(
                self.cuenta_acreedora,
                self.cuenta_deudora
            ),
            'Aumento de crédito'
        )

    def test_si_cuenta_acreedora_tiene_saldo_negativo_e_importe_es_igual_a_saldo_de_cuenta_deudora_devuelve_cancelacion_de_credito(self):
        Movimiento.crear('saldo_ca', 100, None, self.cuenta_acreedora)
        Movimiento.crear('saldo_cd', 100, self.cuenta_deudora)
        self.mov.importe = 100
        self.assertEqual(
            self.mov._concepto_movimiento_credito(
                self.cuenta_acreedora,
                self.cuenta_deudora
            ),
            'Cancelación de crédito'
        )

    def test_si_cuenta_acreedora_tiene_saldo_negativo_e_importe_no_es_igual_a_saldo_de_cuenta_deudora_devuelve_pago_a_cuenta_de_credito(self):
        Movimiento.crear('saldo_ca', 100, None, self.cuenta_acreedora)
        Movimiento.crear('saldo_cd', 100, self.cuenta_deudora)
        self.mov.importe = 80
        self.assertEqual(
            self.mov._concepto_movimiento_credito(
                self.cuenta_acreedora,
                self.cuenta_deudora
            ),
            'Pago a cuenta de crédito'
        )

    def test_si_cuenta_acreedora_tiene_saldo_cero_devuelve_constitucion_de_credito(self):
        self.assertEqual(
            self.mov._concepto_movimiento_credito(
                self.cuenta_acreedora,
                self.cuenta_deudora
            ),
            'Constitución de crédito'
        )



class TestModelMovimientoMetodoGestionarTransferencia(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.tit1 = Titular.tomar(titname='default')
        self.tit2 = Titular.crear(nombre='Titular 2', titname='tit2')
        self.cuenta2 = Cuenta.crear('cuenta tit 2', 'ct2', titular=self.tit2)
        self.mov = Movimiento(
            concepto='traspaso',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2
        )

    @patch('diario.models.Movimiento._crear_movimiento_credito')
    def test_crea_movimiento_credito(self, mock_crear_movimiento_credito):
        self.mov._gestionar_transferencia()
        mock_crear_movimiento_credito.assert_called_once()

    def test_si_receptor_no_es_acreedor_de_emisor_agrega_receptor_como_deudor_de_emisor(self):
        self.mov._gestionar_transferencia()
        self.assertIn(self.tit1, self.tit2.deudores.all())

    def test_si_receptor_es_acreedor_de_emisor_no_agrega_receptor_como_deudor_de_emisor(self):
        Movimiento.crear('prestamo', 200, self.cuenta2, self.cuenta1)
        self.mov._gestionar_transferencia()
        self.assertNotIn(self.tit1, self.tit2.deudores.all())

    @patch('diario.models.Titular.cancelar_deuda_de', autospec=True)
    def test_si_receptor_es_acreedor_de_emisor_y_se_transfiere_el_total_adeudado_cancelar_deuda(self, mock_cancelar_deuda_de):
        Movimiento.crear('prestamo', 100, self.cuenta2, self.cuenta1)
        self.mov._gestionar_transferencia()
        mock_cancelar_deuda_de.assert_called_once_with(self.tit1, self.tit2)

    @patch('diario.models.Titular.cancelar_deuda_de')
    def test_si_receptor_es_acreedor_de_emisor_y_no_se_transfiere_el_total_adeudado_no_cancelar_deuda(self, mock_cancelar_deuda_de):
        Movimiento.crear('prestamo', 200, self.cuenta2, self.cuenta1)
        self.mov._gestionar_transferencia()
        mock_cancelar_deuda_de.assert_not_called()

    def test_si_receptor_es_acreedor_de_emisor_y_se_transfiere_mas_del_total_adeudado_se_invierte_relacion_crediticia(self):
        Movimiento.crear('prestamo', 50, self.cuenta2, self.cuenta1)
        self.mov._gestionar_transferencia()
        self.assertNotIn(self.tit2, self.tit1.deudores.all())
        self.assertIn(self.tit1, self.tit2.deudores.all())

    def test_si_es_un_pago_a_cuenta_no_incluye_emisor_entre_acreedores_de_receptor(self):
        Movimiento.crear('Préstamo', 115, self.cuenta2, self.cuenta1)

        self.mov._gestionar_transferencia()

        self.assertNotIn(self.tit2, self.tit1.acreedores.all())

    def test_si_es_un_pago_a_cuenta_mantiene_emisor_entre_deudores_de_receptor(self):
        Movimiento.crear('Préstamo', 115, self.cuenta2, self.cuenta1)

        self.mov._gestionar_transferencia()

        self.assertIn(self.tit2, self.tit1.deudores.all())

    @patch('diario.models.Titular.cancelar_deuda_de', autospec=True)
    def test_si_emisor_paga_la_totalidad_se_cancela_su_deuda(self, mock_cancelar_deuda_de):
        Movimiento.crear(
            'Préstamo', 100, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)

        self.mov._gestionar_transferencia()

        mock_cancelar_deuda_de.assert_called_once_with(self.tit1, self.tit2)

    def test_si_emisor_paga_mas_de_lo_que_debe_se_lo_elimina_de_deudores_de_receptor(self):
        Movimiento.crear(
            'Préstamo', 16, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)

        self.mov._gestionar_transferencia()

        self.assertNotIn(self.tit2, self.tit1.deudores.all())

    def test_si_emisor_paga_mas_de_lo_que_debe_se_incluye_a_receptor_entre_sus_deudores(self):
        Movimiento.crear(
            'Devolución', 16, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)

        self.mov._gestionar_transferencia()

        self.assertIn(self.tit1, self.tit2.deudores.all())
