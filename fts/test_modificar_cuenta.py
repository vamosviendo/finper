from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from diario.models import Cuenta

from .base import FunctionalTest


class TestModificaCuenta(FunctionalTest):

    def test_puede_modificar_nombre_de_cuenta(self):
        Cuenta.objects.create(nombre='Efetivo')
        self.browser.get(self.live_server_url)
        self.esperar_elemento("link_mod_cuenta", By.CLASS_NAME).click()

        self.esperar_elemento('id_nombre').send_keys(Keys.RIGHT)
        self.esperar_elemento('id_nombre').send_keys(Keys.RIGHT)
        self.esperar_elemento('id_nombre').send_keys(Keys.RIGHT)
        self.esperar_elemento('id_nombre').send_keys('c')
        self.esperar_elemento('id_btn_submit').click()

        nombre = self.esperar_elemento('class_nombre_cuenta', By.CLASS_NAME).text
        self.assertEqual(nombre, 'Efectivo')
