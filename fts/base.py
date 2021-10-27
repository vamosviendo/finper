import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from .driver import esperar, MiFirefox

User = get_user_model()


class FunctionalTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            cls.test_username = os.environ['TEST_USERNAME']
            cls.test_password = os.environ['TEST_PASSWORD']
        except KeyError:
            pass

    def setUp(self):
        super().setUp()
        headless = os.environ.get('HEADLESS')
        if headless:
            FirefoxOptions = webdriver.FirefoxOptions()
            FirefoxOptions.headless = True
            self.browser = MiFirefox(firefox_options=FirefoxOptions)
        else:
            self.browser = MiFirefox()
        # Verifica si se está ejecutando en un entorno local o en un server
        # externo-
        self.staging_server = os.environ.get('STAGING_SERVER')
        if self.staging_server:
            self.live_server_url = f'http://{self.staging_server}'

    def tearDown(self):
        self.browser.quit()
        super().tearDown()

    ### MÉTODOS DE NAVEGACION

    def ir_a_pag(self, url=''):
        self.browser.get(f'{self.live_server_url}{url}')

    ### MÉTODOS DE MANEJO DE FORMULARIOS

    def limpiar_campo(self, id_campo):
        """ Elimina el valor de un campo de form."""
        self.browser.limpiar_campo(id_campo)

    def completar(self, id_campo, texto, criterio=By.ID):
        """ Completa un campo de texto en un form, o selecciona un valor
            de un campo select."""
        self.browser.completar(id_campo, texto, criterio)

    def pulsar(self, boton="id_btn_submit", crit=By.ID):
        """ Busca un botón y lo pulsa."""
        self.browser.pulsar(boton, crit)

    def completar_y_esperar_error(self, campos_y_valores, id_errores, error):
        """ Completa uno o más campos con valores erróneos y espera los
            mensajes de error correspondientes."""

        for clave, valor in campos_y_valores.items():
            self.completar(clave, valor)

        self.pulsar()

        errores = self.espera(
            lambda: self.browser.find_element_by_id(id_errores)
        )
        self.assertIn(error, errores.text)

    ### ASERCIONES

    @staticmethod
    def assertContainsElement(container, element, crit=By.ID):
        """ Lanza un AssertionError si no encuentra el elemento"""
        try:
            container.find_element(crit, element)
        except NoSuchElementException:
            raise AssertionError(
                f'"{container.tag_name}" no contiene ningún elemento '
                f'con id "{element}"'
            )

    ### ESPERAS

    @esperar
    def espera(self, funcion):
        """ Espera el tiempo por default y ejecuta función."""
        return funcion()

    def esperar_elemento(self, elemento, criterio=By.ID):
        return self.browser.esperar_elemento(elemento, criterio)

    def esperar_elementos(self, elementos, criterio=By.CLASS_NAME, fail=True):
        return self.browser.esperar_elementos(elementos, criterio, fail)

    @esperar
    def esperar_que_se_abra(self, elemento, display='flex'):
        self.assertEqual(elemento.value_of_css_property('display'), display)
        return elemento

    @esperar
    def esperar_que_se_cierre(self, elemento):
        self.assertEqual(elemento.value_of_css_property('display'), 'none')
        return elemento

    @esperar
    def esperar_cambio_en_elemento(self, elemento, atributo, valor_anterior,
                                   msj=None, criterio=By.ID):
        """ Dado un elemento web, espera que el valor de un atributo del mismo
            cambie de valor. """
        elem = self.browser.find_element(criterio, elemento)
        self.assertNotEqual(elem.get_attribute(atributo), valor_anterior, msj)
        return elem

    @esperar
    def esperar_lista_de_elementos(
            self, lista, search_str, atributo, criterio=By.CLASS_NAME):
        """ Busca elementos que coincidan con un criterio y arma una lista
            con un atributo de esos elementos. Espera hasta que esta lista
            coincida con una lista dada."""
        webelements = self.browser.esperar_elementos(search_str, criterio)
        atributos = [we.get_attribute(atributo) for we in webelements]
        self.assertEqual(atributos, lista)
        return webelements
