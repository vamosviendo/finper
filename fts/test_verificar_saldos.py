import datetime
from pathlib import Path
from unittest.mock import patch

from fts.base import FunctionalTest

from diario.models import Cuenta, Movimiento
from utils.funciones.archivos import fijar_mtime


class TestVerificarSaldo(FunctionalTest):

    def setUp(self):
        super().setUp()
        self.cuenta1 = Cuenta.crear('Afectivo', 'A')
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
        self.hoy.touch()
        fijar_mtime(self.hoy, datetime.datetime(2021, 4, 4))

    def tearDown(self):
        self.patcherf.stop()

        # Recuperar marca de fecha
        self.hoy.unlink()
        self.ayer.rename('hoy.mark')
        super().tearDown()

    def test_no_cambia_fecha_no_se_verifica_saldo(self):
        self.ir_a_pag()
        saldo = self.esperar_elemento('id_saldo_cta_a').text
        self.assertEqual(saldo, '250.00')

    def test_saldo_no_coincide_corregir_o_agregar_movimiento(self):
        self.fecha = datetime.date(2021, 4, 5)
        self.ir_a_pag()
        mensaje = self.browser.esperar_elemento('id_msj_ctas_erroneas').text
        self.assertIn('afectivo', mensaje)
        self.assertIn('banco', mensaje)
        self.esperar_elementos('class_btn_corregir')[0].click()
        self.esperar_elementos('class_btn_agregar')[0].click()
        saldos = self.esperar_elementos("class_saldo_cuenta")
        self.assertEqual(saldos[0].text, '200.00')
        self.assertEqual(saldos[1].text, '400.00')
        movs_concepto = self.esperar_elementos('class_td_concepto')
        movs_importe = self.esperar_elementos('class_td_importe')
        self.assertIn('Movimiento correctivo', [c.text for c in movs_concepto])
        self.assertIn('600.00', [i.text for i in movs_importe])

    def test_cuenta_caja_no_muestra_movimiento_correctivo(self):
        # Dada una cuenta con dos subcuentas y saldo erróneo
        self.cuenta1.corregir_saldo()
        self.cuenta2.corregir_saldo()
        cuenta3 = Cuenta.crear('Banco Nación', 'bn')
        Movimiento.crear('Ingreso', 500, cta_entrada=cuenta3)
        cuenta3.dividir_entre(
            {
                'nombre': 'Banco Nación Caja de Ahorro',
                'slug': 'bnca',
                'saldo': 200,
            },
            {
                'nombre': 'Banco Nación Cuenta Corriente',
                'slug': 'bncc',
            }
        )
        cuenta3.saldo = 600
        cuenta3.save()

        # Al cambiar la fecha se detecta el saldo erróneo y se indica que
        # debe ser corregido.
        self.fecha = datetime.date(2021, 4, 5)
        self.ir_a_pag()
        mensaje = self.browser.esperar_elemento('id_msj_ctas_erroneas').text
        self.assertIn('banco nación', mensaje)

        # Al ser una cuenta acumulativa, no aparece el botón de agregar
        # movimiento
        self.assertEqual(
            len(self.esperar_elementos('class_btn_agregar', fail=False)), 0,
            'Aparece botón "agregar movimiento" en una cuenta que no los admite'
        )

        # Si cliqueamos en el botón de corregir saldo, aparece el saldo
        # corregido
        self.esperar_elementos('class_btn_corregir')[0].click()
        saldo = self.esperar_elemento('id_saldo_cta_bn').text
        self.assertEqual(saldo, '500.00')


