import time

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from django.test import LiveServerTestCase

MAX_WAIT = 2


def esperar(condicion):

    def condicion_modificada(*args, **kwargs):
        arranque = time.time()
        while True:
            try:
                return condicion(*args, **kwargs)
            except (AssertionError, WebDriverException) as noesperomas:
                if time.time() - arranque > MAX_WAIT:
                    raise noesperomas
                time.sleep(0.2)

    return condicion_modificada


class FunctionalTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.get(self.live_server_url)

    def tearDown(self) -> None:
        self.browser.quit()

    @esperar
    def espera(self, funcion):
        return funcion()

    @esperar
    def esperar_movimiento_en_tabla(self, concepto):
        tabla = self.browser.find_element_by_id('id_table_movs')
        celdas = tabla.find_elements_by_tag_name('td')
        self.assertIn(concepto, [celda.text for celda in celdas])