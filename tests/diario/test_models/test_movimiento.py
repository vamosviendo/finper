from datetime import date
from unittest import skip
from unittest.mock import patch, call

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Cuenta, CuentaInteractiva, Movimiento, Titular, Saldo
from utils import errors


class TestModelMovimiento(TestCase):

    def setUp(self):
        self.cuenta1 = Cuenta.crear(nombre='Cuenta titular 1', slug='ct1')


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
        self.cuenta2 = Cuenta.crear(nombre='Cuenta 2', slug='ct2')
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

    @patch('diario.models.movimiento.Saldo.registrar')
    def test_registra_movimiento_en_saldos_historicos(self, mock_registrar):
        Movimiento.crear(
            'Nuevo mov', 20, self.cuenta1, fecha=date(2011, 11, 15))
        mock_registrar.assert_called_once_with(
            cuenta=self.cuenta1,
            fecha=date(2011, 11, 15),
            importe=20
        )

    @patch('diario.models.movimiento.Saldo.registrar')
    def test_pasa_importe_en_negativo_a_registrar_saldo_si_cuenta_es_de_salida(self, mock_registrar):
        Movimiento.crear(
            'Nuevo mov', 20, cta_salida=self.cuenta1, fecha=date(2011, 11, 15))
        mock_registrar.assert_called_once_with(
            cuenta=self.cuenta1,
            fecha=date(2011, 11, 15),
            importe=-20
        )

    def test_integrativo_crear_movimiento_en_fecha_antigua_modifica_saldos_de_fechas_posteriores(self):
        Movimiento.crear(
            'Movimiento anterior', 30, self.cuenta1, fecha=date(2011, 11, 11))

        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, fecha=date(2011, 11, 15)).importe,
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
                nombre='Préstamo entre tit2 y default',
                slug='_tit2-default',
                titular=self.titular2
            )
        )
        args2 = mock_crear.call_args_list[1][1]
        args2.pop('contracuenta')
        self.assertEqual(
            args2,
            dict(
                nombre='Préstamo entre default y tit2',
                slug='_default-tit2',
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

    def test_guarda_marcador_al_movimiento_de_credito_generado(self):
        movimiento = Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        mov_credito = Movimiento.tomar(concepto='Constitución de crédito')
        self.assertEqual(movimiento.id_contramov, mov_credito.id)

    def test_movimiento_generado_se_marca_como_automatico(self):
        movimiento = Movimiento.crear(
            'Prestamo', 10, cta_entrada=self.cuenta1, cta_salida=self.cuenta2)
        mov_credito = Movimiento.tomar(id=movimiento.id_contramov)
        self.assertTrue(mov_credito.es_automatico)

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


class TestModelMovimientoCrearEntreTitularesSiguientes(
        TestModelMovimientoCrearEntreTitulares):

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
        self.assertEqual(Cuenta.tomar(slug='_tit2-default').saldo, 4)

    def test_suma_importe_a_cuenta_deuda_en_movimiento_inverso_entre_titulares_con_credito_existente(self):
        Movimiento.crear('Devolución', 6, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)
        self.assertEqual(Cuenta.tomar(slug='_default-tit2').saldo, -4)

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

    def test_si_toma_credito_despues_de_cancelarlo_asunto_del_movimiento_es_Constitucion_de_credito(self):
        Movimiento.crear(
            'Devolución', 10, cta_entrada=self.cuenta2, cta_salida=self.cuenta1)

        mov = Movimiento.crear(
            'Nuevo préstamo',
            10,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2
        )
        self.assertEqual(
            Movimiento.tomar(id=mov.id_contramov).concepto,
            'Constitución de crédito'
        )

    def test_si_se_genera_contramovimiento_en_fecha_distinta_de_movimiento_toma_fecha_de_movimiento(self):
        movi = Movimiento.crear(
            'Traspaso', 10,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta2,
            fecha=date(2020, 10, 2),
            esgratis=True
        )
        movi.esgratis = False
        movi.full_clean()
        movi.save()

        self.assertEqual(
            Movimiento.tomar(id=movi.id_contramov).fecha,
            date(2020, 10, 2)
        )


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
        self.cuenta2 = Cuenta.crear('cuenta 2', 'c2')
        self.cuenta3 = Cuenta.crear(
            'Cuenta otro titular', 'ct2', titular=self.titular2)
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


class TestModelMovimientoEliminar(TestModelMovimientoSave):

    def test_eliminar_movimiento_resta_de_saldo_cta_entrada_y_suma_a_saldo_cta_salida(self):

        self.mov1.delete()
        self.cuenta1.refresh_from_db(fields=['_saldo'])

        self.assertEqual(self.cuenta1.saldo, 140-125)
        saldo1 = self.cuenta1.saldo

        self.mov3.delete()
        self.cuenta1.refresh_from_db(fields=['_saldo'])
        self.cuenta2.refresh_from_db(fields=['_saldo'])

        self.assertEqual(self.cuenta2.saldo, -50+50)
        self.assertEqual(self.cuenta1.saldo, 15-50)

    def test_eliminar_movimiento_no_unico_de_cuenta_en_fecha_pasa_importe_en_negativo_a_registrar_saldo_cta_entrada(self):
        fecha_mov = self.mov1.fecha
        Movimiento.crear(
            'Otro mov en fecha', 100, self.cuenta1, fecha=fecha_mov)
        with patch(
                'diario.models.movimiento.Saldo.registrar') as mock_registrar:
            self.mov1.delete()
            mock_registrar.assert_called_once_with(
                cuenta=Cuenta.objects.get_no_poly(pk=self.cuenta1.pk),
                fecha=fecha_mov,
                importe=-125
            )

    def test_eliminar_movimiento_no_unico_de_cuenta_en_fecha_pasa_importe_en_positivo_a_registrar_saldo_cta_salida(self):
        fecha_mov = self.mov2.fecha
        Movimiento.crear(
            'Otro mov en fecha', 100, self.cuenta1, fecha=fecha_mov)
        with patch('diario.models.movimiento.Saldo.registrar') as mock_registrar:
            self.mov2.delete()
            mock_registrar.assert_called_once_with(
                cuenta=Cuenta.objects.get_no_poly(pk=self.cuenta1.pk),
                fecha=fecha_mov,
                importe=35
            )

    def test_eliminar_movimiento_no_unico_de_cuenta_en_fecha_resta_importe_de_saldo_de_cta_entrada_de_la_fecha_del_mov_eliminado(self):
        fecha_mov = self.mov1.fecha
        Movimiento.crear(
            'Otro mov en fecha', 100, self.cuenta1, fecha=fecha_mov)
        self.mov1.delete()
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, fecha=fecha_mov).importe,
            100
        )

    def test_eliminar_movimiento_no_unico_de_cuenta_en_fecha_suma_importe_a_saldo_de_cta_salida_de_la_fecha_del_mov_eliminado(self):
        fecha_mov = self.mov2.fecha
        Movimiento.crear(
            'Otro mov en fecha', 100, self.cuenta1, fecha=fecha_mov)
        self.mov2.delete()
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, fecha=fecha_mov).importe,
            225
        )

    def test_eliminar_movimiento_no_unico_de_cuenta_en_fecha_resta_importe_de_saldos_de_cta_entrada_posteriores_a_la_fecha_del_mov_eliminado(self):
        fecha_mov = self.mov1.fecha
        Movimiento.crear(
            'Otro mov en fecha', 100, self.cuenta1, fecha=fecha_mov)
        self.mov1.delete()
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, fecha=self.mov2.fecha).importe,
            65
        )
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, fecha=self.mov3.fecha).importe,
            115
        )

    def test_eliminar_movimiento_no_unico_de_cuenta_en_fecha_suma_importe_a_saldos_de_cta_salida_posteriores_a_la_fecha_del_mov_eliminado(self):
        fecha_mov = self.mov2.fecha
        Movimiento.crear('Otro mov en fecha', 100, self.cuenta1, fecha=fecha_mov)
        self.mov2.delete()
        self.assertEqual(
            Saldo.tomar(cuenta=self.cuenta1, fecha=self.mov3.fecha).importe,
            275
        )

    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_eliminar_unico_movimiento_de_cta_entrada_en_fecha_elimina_saldo_de_cuenta_en_fecha(self, mock_eliminar):
        fecha_mov = self.mov1.fecha
        self.mov1.delete()
        mock_eliminar.assert_called_once_with(
            Saldo.tomar(cuenta=self.cuenta1, fecha=fecha_mov)
        )

    @patch('diario.models.movimiento.Saldo.eliminar', autospec=True)
    def test_eliminar_unico_movimiento_de_cta_salida_en_fecha_elimina_saldo_de_cuenta_en_fecha(self, mock_eliminar):
        fecha_mov = self.mov2.fecha
        self.mov2.delete()
        mock_eliminar.assert_called_once_with(
            Saldo.tomar(cuenta=self.cuenta1, fecha=fecha_mov)
        )

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

    def test_no_permite_eliminar_contramovimientos(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        with self.assertRaisesMessage(
                ValidationError,
                'No se puede eliminar movimiento automático'):
            contramov.delete()

    def test_permite_eliminar_contramovimiento_con_force_true(self):
        movimiento = Movimiento.crear(
            'Préstamo', 30, self.cuenta3, self.cuenta1)
        contramov = Movimiento.tomar(id=movimiento.id_contramov)
        try:
            contramov.delete(force=True)
        except errors.ErrorMovimientoAutomatico:
            raise AssertionError(
                'No se eliminó contramovimiento a pesar de force=True')


class TestModelMovimientoPropiedadSentido(TestModelMovimiento):

    @skip
    def test_eliminar(self):
        self.fail('Eliminar')

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
        self.assertTrue(mov.es_prestamo())

    def test_devuelve_false_si_mov_no_es_traspaso(self):
        mov = Movimiento.crear('entrada', 100, self.cuenta1)
        self.assertFalse(mov.es_prestamo())

    def test_devuelve_false_si_cuentas_pertenecen_al_mismo_titular(self):
        mov = Movimiento.crear('traspaso', 100, self.cuenta2, self.cuenta3)
        self.assertFalse(mov.es_prestamo())

    def test_devuelve_false_si_mov_es_gratis(self):
        mov = Movimiento.crear(
            concepto='traspaso',
            importe=100,
            cta_entrada=self.cuenta1,
            cta_salida=self.cuenta3,
            esgratis=True
        )
        self.assertFalse(mov.es_prestamo())


class TestModelMovimientoMetodoHermanosDeFecha(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.mov1 = Movimiento.crear(
            'Movimiento 1', 100, self.cuenta1, fecha=date(2011, 11, 11))
        self.mov2 = Movimiento.crear(
            'Movimiento 2', 200, self.cuenta1, fecha=date(2011, 11, 11))
        self.mov3 = Movimiento.crear(
            'Movimiento 3', 300, self.cuenta1, fecha=date(2011, 11, 11))
        self.result = self.mov1.hermanos_de_fecha()

    def test_devuelve_movimientos_de_la_fecha(self):
        self.assertIn(self.mov2, self.result)
        self.assertIn(self.mov3, self.result)

    def test_no_incluye_instancia(self):
        self.assertNotIn(self.mov1, self.result)

    def test_no_incluye_movimientos_de_otra_fecha(self):
        mov4 = Movimiento.crear(
            'Movimiento 4', 400, self.cuenta1, fecha=date(2011, 11, 12))
        self.assertNotIn(mov4, self.result)


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
        self.assertTrue(self.mov1._cambia_campo('importe', 'fecha'))

    def test_devuelve_false_si_no_hay_cambio_en_ninguno_de_los_campos_dados(self):
        self.assertFalse(self.mov1._cambia_campo('concepto', 'fecha'))


@patch('diario.models.Movimiento.mantiene_foreignfield', autospec=True)
class TestModelMovimientoMetodoMantieneCuenta(TestModelMovimiento):

    def setUp(self):
        super().setUp()
        self.entrada = Movimiento.crear('entrada', 100, self.cuenta1)

    def test_llama_a_mantiene_foreignkey_con_cuenta_y_movimiento(self, mock_mantiene_foreignfield):
        mov_guardado = self.entrada
        self.entrada._mantiene_cuenta('cta_entrada', mov_guardado)
        mock_mantiene_foreignfield.assert_called_once_with(
            self.entrada, 'cta_entrada', mov_guardado
        )

    def test_devuelve_resultado_de_mantiene_foreignkey(self, mock_mantiene_foreignkey):
        mov_guardado = self.entrada
        mock_mantiene_foreignkey.return_value = True
        self.assertTrue(
            self.entrada._mantiene_cuenta('cta_entrada', mov_guardado)
        )
        mock_mantiene_foreignkey.return_value = False
        self.assertFalse(
            self.entrada._mantiene_cuenta('cta_entrada', mov_guardado)
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

    def test_si_receptor_no_es_acreedor_de_emisor_agregar_receptor_como_deudor_de_emisor(self):
        self.mov._gestionar_transferencia()
        self.assertIn(self.tit1, self.tit2.deudores.all())

    def test_si_receptor_es_acreedor_de_emisor_no_agregar_receptor_como_deudor_de_emisor(self):
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
