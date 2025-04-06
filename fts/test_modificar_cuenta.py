from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from diario.models import Cuenta

from .base import FunctionalTest


class TestModificaCuenta(FunctionalTest):

    def test_puede_modificar_nombre_de_cuenta(self):
        Cuenta.crear(nombre='Efetivo', sk='E')
        self.ir_a_pag()
        self.pulsar("link_mod_cuenta", By.CLASS_NAME)

        for x in range(4):
            self.esperar_elemento('id_nombre').send_keys(Keys.LEFT)
        self.esperar_elemento('id_nombre').send_keys('c')
        self.pulsar()

        nombre = self.esperar_elemento('class_nombre_cuenta', By.CLASS_NAME).text
        self.assertEqual(nombre, 'efectivo')
