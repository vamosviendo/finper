from selenium.webdriver.common.by import By

from diario.models import Cuenta, Movimiento

from .base import FunctionalTest


class TestDividirCuenta(FunctionalTest):

    def test_puede_dividir_cuenta_en_subcuentas(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        Movimiento.crear(
            concepto='Saldo al inicio', importe=200, cta_entrada=cta1
        )
        self.ir_a_pag()
        self.pulsar("link_mod_cuenta", By.CLASS_NAME)

        self.pulsar('id_btn_dividir')
        self.completar('id_form-0-nombre', 'Cajón de arriba')
        self.completar('id_form-0-slug', 'ecar')
        self.completar('id_form-0-saldo', 150)
        self.completar('id_form-1-nombre', 'Billetera')
        self.completar('id_form-1-slug', 'ebil')
        self.completar('id_form-1-saldo', 50)
        self.pulsar()

        saldo = self.esperar_elemento('id_saldo_cta_e').text
        self.assertEqual(saldo, '200.00')

        nombres = [e.text for e in self.esperar_elementos('class_nombre_cuenta')]
        saldos = [s.text for s in self.esperar_elementos('class_saldo_cuenta')]
        self.assertEqual(nombres[0], 'billetera')
        self.assertEqual(saldos[0], '50.00')
        self.assertEqual(nombres[1], 'cajón de arriba')
        self.assertEqual(saldos[1], '150.00')

        self.ir_a_pag()

        movs = self.esperar_elementos('class_row_mov')
        self.assertEqual(len(movs), 5)
        conceptos = [
            c.text for c in self.esperar_elementos('class_td_concepto')]
        importes = [i.text for i in self.esperar_elementos('class_td_importe')]
        cuentas = [c.text for c in self.esperar_elementos('class_td_cuentas')]
        map(
            lambda c: self.assertEqual(
                c, 'Saldo al inicio', 'Concepto equivocado'),
            conceptos
        )
        self.assertEqual(importes[1], '150.00')
        self.assertEqual(importes[2], '50.00')
        self.assertEqual(importes[3], '150.00')
        self.assertEqual(importes[4], '50.00')

        self.assertEqual(cuentas[1], '-efectivo')
        self.assertEqual(cuentas[2], '-efectivo')
        self.assertEqual(cuentas[3], '+cajón de arriba')
        self.assertEqual(cuentas[4], '+billetera')

        nombre = self.esperar_elemento(
            'class_nombre_cuenta', By.CLASS_NAME).text
        self.assertEqual(nombre, 'efectivo')
