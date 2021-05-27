from selenium.webdriver.common.by import By

from diario.models import Cuenta, Movimiento

from .base import FunctionalTest


class TestModificaCuenta(FunctionalTest):

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
        self.completar('id_form-0-saldo', 120)
        self.completar('id_form-1-nombre', 'Billetera')
        self.completar('id_form-1-slug', 'ebil')
        self.completar('id_form-1-saldo', 50)
        self.completar('id_form-2-nombre', 'Canuto')
        self.completar('id_form-2-slug', 'ecan')
        self.pulsar()

        saldo = self.esperar_elemento('id_div_saldo_e')
        self.assertEqual(saldo, '200.00')

        nombres = self.esperar_elementos('class_nombre_cuenta')
        saldos = self.esperar_elementos('class_saldo_cuenta')
        self.assertEqual(nombres[0], 'Cajón de arriba')
        self.assertEqual(saldos[0], '120.00')
        self.assertEqual(nombres[1], 'Billetera')
        self.assertEqual(saldos[1], '50.00')
        self.assertEqual(nombres[2], 'Canuto')
        self.assertEqual(saldos[2], '30.00')

        self.ir_a_pag()

        movs = self.esperar_elementos('class_row_mov')
        self.assertEqual(len(movs), 4)
        conceptos = [
            c.text for c in self.esperar_elementos('class_td_concepto')]
        importes = [i.text for i in self.esperar_elementos('class_td_importe')]
        cuentas = [c.text for c in self.esperar_elementos('class_td_cuentas')]
        map(
            lambda c: self.assertEqual(
                c, 'Saldo al inicio', 'Concepto equivocado'),
            conceptos
        )
        self.assertEqual(importes[1], '120.00')
        self.assertEqual(importes[2], '50.00')
        self.assertEqual(importes[3], '30.00')

        self.assertEqual(cuentas[1], '-Efectivo +Cajón de arriba')
        self.assertEqual(cuentas[2], '-Efectivo +Billetera')
        self.assertEqual(cuentas[3], '-Efectivo +Canuto')

        nombre = self.esperar_elemento('class_nombre_cuenta', By.CLASS_NAME).text
        self.assertEqual(nombre, 'Efectivo')
