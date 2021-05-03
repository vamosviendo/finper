import os, time
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, \
    WebDriverException, InvalidElementStateException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

User = get_user_model()


def esperar(condicion, tiempo=10):
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


class MiWebElement(WebElement):

    def contiene_elemento(self, elemento, criterio=By.ID, debug=False):
        """ Devuelve True si encuentra elemento en obj MiWebElement."""
        if debug:
            print('TEXT:', self.text)
            print('HTML:', self.get_attribute('innerHTML'))

        try:
            self.find_element(criterio, elemento)
            return True
        except NoSuchElementException:
            return False

    def ocupa_espacio(self):
        if self.value_of_css_property("width") in ["0", "0px", "0%"]:
            return False
        if self.value_of_css_property("display") == ("none"):
            return False
        return True

    def es_visible(self):
        if not self.ocupa_espacio():
            return False
        if self.value_of_css_property("opacity") == "0%":
            return False
        if self.value_of_css_property("visibility") == "hidden":
            return False
        if not self.is_displayed():
            return False
        return True

    def int_css_prop(self, cssprop):
        """ Devuelve el valor de una propiedad css numérica como int."""
        return int(self.value_of_css_property(cssprop).rstrip('px%'))

    def innerWidth(self):
        """ Devuelve el ancho interior de un elemento, sin contar
            padding ni border."""
        if self.value_of_css_property('box-sizing') == 'content-box':
            return int(self.size.get('width')) - (
                    self.int_css_prop('padding-left') +
                    self.int_css_prop('padding-right') +
                    self.int_css_prop('border-left-width') +
                    self.int_css_prop('border-right-width')
            )
        else:
            return int(self.size.get('width'))

    def outerWidth(self):
        """ Devuelve el ancho externo de un elemento, incluyendo padding,
            border y margin."""
        if self.value_of_css_property('box-sizing') == 'border-box':
            return int(self.size.get('width')) + (
                    self.int_css_prop('padding-left') +
                    self.int_css_prop('padding-right') +
                    self.int_css_prop('border-left-width') +
                    self.int_css_prop('border-right-width') +
                    self.int_css_prop('margin-left') +
                    self.int_css_prop('margin-right')
            )
        else:
            return int(self.size.get('width')) + (
                    self.int_css_prop('margin-left') +
                    self.int_css_prop('margin-right')
            )

    def img_url(self):
        """ A partir del atributo src de una imagen, devuelve el url
        del campo ImageField correspondiente."""
        src = self.get_attribute('src')
        return urlparse(src).path

    def img_filename(self):
        """ A partir del atributo src de una imagen, devuelve el nombre de
            archivo del campo ImageField correspondiente."""
        return self.img_url()[len('/media/'):]


    @esperar
    def esperar_elemento(self, elemento, criterio=By.ID):
        return self.find_element(criterio, elemento)

    @esperar
    def esperar_elementos(self, search_str, criterio=By.CLASS_NAME):
        elementos = self.find_elements(criterio, search_str)
        assert(len(elementos) != 0)
        return elementos


class MiFirefox(webdriver.Firefox):
    _web_element_cls = MiWebElement

    def movermouse(self, horiz, vert):
        """ Dispara un movimiento del ratón."""
        webdriver.ActionChains(self).move_by_offset(horiz, vert).perform()

    @esperar
    def esperar_elemento(self, elemento, criterio=By.ID):
        return self.find_element(criterio, elemento)

    @esperar
    def esperar_elementos(self, search_str, criterio=By.CLASS_NAME):
        elementos = self.find_elements(criterio, search_str)
        assert len(elementos) != 0, \
            f'no se encontraron elementos coincidentes con {search_str}'
        return elementos


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
        self.browser.find_element_by_id(id_campo).clear()

    def completar(self, id_campo, texto):
        """ Completa un campo de texto en un form, o selecciona un valor
            de un campo select."""
        campo = self.esperar_elemento(id_campo)
        try:
            self.limpiar_campo(id_campo)
            campo.send_keys(str(texto))
        except InvalidElementStateException:
            Select(campo).select_by_visible_text(texto)

    def pulsar(self, boton="id_btn_submit", crit=By.ID):
        """ Busca un botón y lo pulsa."""
        self.browser.find_element(crit, boton).click()

    def completar_y_esperar_error(self, campos_y_valores, id_errores, error):
        """ Completa uno o más campos con valores erróneos y espera los
            mensajes de error correspondientes."""

        for clave, valor in campos_y_valores.items():
            self.completar_campo_o_seleccionar(clave, valor)

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

    def esperar_elementos(self, elementos, criterio=By.CLASS_NAME):
        return self.browser.esperar_elementos(elementos, criterio)

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
