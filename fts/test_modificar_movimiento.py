from selenium.webdriver.common.by import By

from diario.models import Cuenta, Movimiento

from .base import FunctionalTest


class TestModificaMovimiento(FunctionalTest):

    def setUp(self):
        super().setUp()
        self.cta1 = Cuenta.crear(nombre='Afectivo', slug='A')
        self.mov1 = Movimiento.crear(
            concepto='aSaldo', importe=200, cta_entrada=self.cta1)
        self.ir_a_pag()
        self.saldo = self.esperar_elemento('id_saldo_cta_a').text

    def pulsar(self, boton='link_mod_mov', crit=By.CLASS_NAME):
        super().pulsar(boton, crit)

    def test_puede_modificar_movimiento(self):
        self.pulsar()

        self.completar('id_concepto', 'Saldo inicial')

        self.esperar_elemento('id_btn_submit').click()

        nombre = self.esperar_elemento('class_td_concepto', By.CLASS_NAME).text
        self.assertEqual(nombre, 'Saldo inicial')
        self.assertEqual(
            self.esperar_elemento('id_saldo_cta_a').text, self.saldo)

    def test_modificaciones_en_saldos_y_cuentas(self):
        cta2 = Cuenta.crear('Banco', 'B')
        mov2 = Movimiento.crear(concepto='bSaldo', importe=150, cta_salida=cta2)
        mov3 = Movimiento.crear(
            concepto='cDepósito', importe=70,
            cta_entrada=cta2, cta_salida=self.cta1
        )
        self.ir_a_pag()

        links_mod_movs = self.esperar_elementos('link_mod_mov')
        links_mod_movs[0].click()
        self.completar('id_importe', 100)
        super().pulsar()
        saldo1 = self.esperar_elemento('id_saldo_cta_a').text
        self.assertEqual(saldo1, '30.00')

        links_mod_movs = self.esperar_elementos('link_mod_mov')
        links_mod_movs[1].click()
        self.completar('id_cta_salida', 'Afectivo')
        super().pulsar()
        saldo1 = self.esperar_elemento('id_saldo_cta_a').text
        saldo2 = self.esperar_elemento('id_saldo_cta_b').text
        self.assertEqual(saldo1, '-120.00')
        self.assertEqual(saldo2, '70.00')
