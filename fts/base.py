import time

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from django.test import LiveServerTestCase


def esperar(condicion, tiempo=2):
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


class FunctionalTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.get(self.live_server_url)

    def tearDown(self) -> None:
        self.browser.quit()

    @esperar
    def espera(self, funcion):
        return funcion()
