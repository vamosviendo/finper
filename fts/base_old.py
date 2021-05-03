import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By


def esperar(condicion, tiempo=2):
    """ Devuelve una función que espera un tiempo
        que se cumpla una condición.
        Requiere: time
                  selenium.common.exceptions.WebDriverException
    """

    def condicion_modificada(*args, **kwargs):
        arranque = time.time()
        while True:
            try:
                return condicion(*args, **kwargs)
            except (AssertionError, WebDriverException) as noesperomas:
                if time.time() - arranque > tiempo:
                    raise noesperomas
                time.sleep(0.2)

    return condicion_modificada


class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        super().setUp()
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    @esperar
    def esperar_elemento(self, elemento, criterio=By.ID):
        return self.browser.find_element(criterio, elemento)

    @esperar
    def esperar_elementos(self, elementos, criterio=By.CLASS_NAME):
        result = self.browser.find_elements(criterio, elementos)
        self.assertNotEqual(len(result), 0)
        return result
