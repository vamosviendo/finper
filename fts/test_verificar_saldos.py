import datetime
import os
from pathlib import Path
from unittest.mock import patch

from fts.base import FunctionalTest

from diario.models import Cuenta, Movimiento


@patch('diario.views.verificar_saldos')
class TestVerificarSaldo(FunctionalTest):

    def setUp(self):
        super().setUp()
        self.cuenta1 = Cuenta.crear('Efectivo', 'E')
        self.cuenta2 = Cuenta.crear('Banco', 'B')
        Movimiento.crear(
            fecha= datetime.date(2021, 4, 3), concepto='Saldo inicial',
            importe=200, cta_entrada=self.cuenta1, cta_salida=self.cuenta2,
        )
        self.cuenta1.saldo = 250
        self.cuenta1.save()
        self.cuenta2.saldo = 400
        self.cuenta2.save()

        self.fecha = datetime.date(2021, 4, 4)

        class FalsaFecha(datetime.date):
            @classmethod
            def today(cls):
                return self.fecha

        self.patcherf = patch('datetime.date', FalsaFecha)
        self.patcherf.start()

        # Preservar marca de fecha real
        self.hoy = Path('hoy.mark')
        self.ayer = self.hoy.rename('ayer.mark')
        with open('hoy.mark', 'w'):
            pass

        os.utime(
            'hoy.mark',
            (
                self.hoy.stat().st_ctime,
                datetime.datetime.timestamp(datetime.datetime(2021, 4, 4))
            )
        )

    def tearDown(self):
        self.patcherf.stop()

        # Recuperar marca de fecha
        self.hoy.unlink()
        self.ayer.rename('hoy.mark')
        super().tearDown()

    def test_no_cambia_fecha_no_se_verifica_saldo(self, mock_verificar_saldos):
        self.ir_a_pag()
        saldo = self.esperar_elemento('id_saldo_cta_e').text
        self.assertEqual(saldo, '250.00')

    def test_saldo_no_coincide_corregir_o_agregar_movimiento(self, mock_verificar_saldos):
        mock_verificar_saldos.return_value = [self.cuenta1, self.cuenta2, ]
        self.fecha = datetime.date(2021, 4, 5)
        self.ir_a_pag()
        mensaje = self.browser.esperar_elemento('id_msj_ctas_erroneas').text
        self.assertIn('Efectivo', mensaje)
        self.assertIn('Banco', mensaje)
        self.esperar_elementos('class_btn_corregir')[0].click()
        self.esperar_elementos('class_btn_agregar')[0].click()
        saldos = self.esperar_elementos("class_saldo_cuenta")
        self.assertEqual(saldos[0].text, '200.00')
        self.assertEqual(saldos[1].text, '-200.00')
