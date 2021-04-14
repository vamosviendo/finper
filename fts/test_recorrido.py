import time

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By


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


class TestRecorrido(LiveServerTestCase):

    def setUp(self):
        super().setUp()
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    @esperar
    def esperar_elemento(self, elemento, criterio=By.ID):
        return self.browser.find_element(criterio, elemento)

    def test_recorrido_del_sitio(self):

        self.browser.get(self.live_server_url)

        """ La primera vez que entramos al sitio nos encontramos con:
            - Una sección de totales generales con tres apartados: activo,
                pasivo y saldo. Todos en cero. (1)
            - Una sección de cuentas, vacía. Con solamente un botón para 
                agregar cuentas nuevas. (2)
            - Una lista de últimos movimientos, también vacía, con un botón
                para agregar movimientos. (3)
        """
        # (1) Totales generales:
        totales = self.browser.find_elements_by_class_name('class_div_totales')
        self.assertSetEqual(
            set(tot.get_attribute('id') for tot in totales),
            {'id_div_activo', 'id_div_pasivo', 'id_div_saldo_gral'}
        )

        for elem in totales:
            self.assertEqual(
                elem.find_element_by_id(
                    elem.get_attribute('id').replace('div', 'importe')).text,
                '0,00'
            )

        # (2) Cuentas (vacío):
        grid_cuentas = self.browser.find_element_by_id('id_grid_cuentas')
        cuentas = grid_cuentas.find_elements_by_class_name('class_div_cuenta')
        self.assertEqual(len(cuentas), 0)

        # (3) Lista movimientos (vacío)
        lista_ult_movs = self.browser.find_element_by_id('id_lista_ult_movs')
        ult_movs = lista_ult_movs.find_elements_by_tag_name('li')
        self.assertEqual(len(ult_movs), 0)

        self.browser.find_element_by_id('id_btn_cta_nueva').click()

        self.esperar_elemento('id_input_nombre')