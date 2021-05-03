from selenium.webdriver.common.by import By

from diario.models import Cuenta, Movimiento

from .base import FunctionalTest


class TestModificaMovimiento(FunctionalTest):

    def test_puede_modificar_movimiento(self):
        cta = Cuenta.crear(nombre='Efectivo', slug='E')
        Movimiento.crear(concepto='Saldo', importe=200, cta_entrada=cta)
        self.ir_a_pag()
        saldo = self.esperar_elemento('id_saldo_cta_e').text
        self.pulsar("link_mod_mov", By.CLASS_NAME)

        self.completar('id_concepto', 'Saldo inicial')

        self.esperar_elemento('id_btn_submit').click()

        nombre = self.esperar_elemento('class_td_concepto', By.CLASS_NAME).text
        self.assertEqual(nombre, 'Saldo inicial')
        self.assertEqual(self.esperar_elemento('id_saldo_cta_e').text, saldo)

