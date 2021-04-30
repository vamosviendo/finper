from selenium.webdriver.common.by import By

from diario.models import Cuenta, Movimiento

from .base import FunctionalTest


class TestEliminaCuenta(FunctionalTest):

    def test_puede_eliminar_cuentas(self):
        Cuenta.objects.create(nombre='Efectivo', slug='E')
        Cuenta.objects.create(nombre='Caja de ahorro', slug='ca')
        self.browser.get(self.live_server_url)
        self.esperar_elemento('link_elim_cuenta', By.CLASS_NAME).click()

        self.esperar_elemento('id_btn_confirm').click()

        cuentas = self.esperar_elementos('class_div_cuenta')
        self.assertEqual(len(cuentas), 1)

    def test_no_permite_eliminar_si_el_saldo_no_es_cero(self):
        cta1 = Cuenta.objects.create(nombre='Efectivo', slug='E')
        cta2 = Cuenta.objects.create(nombre='Caja de ahorro', slug='ca')
        Movimiento.objects.create(
            concepto='saldo', importe=100, cta_entrada=cta1)
        self.browser.get(self.live_server_url)
        self.esperar_elemento('link_elim_cuenta', By.CLASS_NAME).click()

        errores = self.esperar_elemento('id_errores')
        self.assertIn('No se puede eliminar cuenta con saldo', errores.text)
