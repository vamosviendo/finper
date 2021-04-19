import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils.datetime_safe import date
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


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


class TestRecorrido(StaticLiveServerTestCase):

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

        # (3) Lista movimientos (vacío)
        lista_ult_movs = self.browser.find_element_by_id('id_lista_ult_movs')
        ult_movs = lista_ult_movs.find_elements_by_tag_name('li')
        self.assertEqual(len(ult_movs), 0)

        # Lo primero que hacemos es agregar una cuenta a la cual podamos
        # cargarle movimientos.
        grid_cuentas.find_element_by_id('id_btn_cta_nueva').click()

        self.esperar_elemento('id_input_nombre').send_keys("Efectivo")
        self.esperar_elemento('id_btn_submit').click()

        # Aparece una caja para la nueva cuenta, con saldo cero
        cuentas = self.esperar_elementos('class_div_cuenta')
        self.assertEqual(len(cuentas), 1)

        self.assertEqual(
            cuentas[0].find_element_by_class_name('class_nombre_cuenta').text,
            'Efectivo'
        )
        self.assertEqual(
            cuentas[0].find_element_by_class_name('class_saldo_cuenta').text,
            '0.00'
        )

        # Cargamos saldo a la cuenta por medio de un movimiento
        lista_ult_movs = self.esperar_elemento('id_lista_ult_movs')
        lista_ult_movs.find_element_by_id('id_btn_mov_nuevo').click()

        # El campo fecha tiene por defecto la fecha del día.
        fecha = self.esperar_elemento('id_input_fecha')
        self.assertEqual(
            fecha.get_attribute('value'),
            date.today().strftime('%Y-%m-%d')
        )
        self.esperar_elemento('id_input_concepto').send_keys(
            'Carga de saldo inicial')
        self.esperar_elemento('id_input_importe').send_keys('985.5')
        cta_entrada = self.esperar_elemento('id_cta_entrada')
        Select(cta_entrada).select_by_visible_text('Efectivo')
        self.esperar_elemento('id_btn_submit').click()

        # El movimiento aparece en la lista de últimos movimientos
        lista_ult_movs = self.browser.find_element_by_id('id_lista_ult_movs')
        ult_movs = lista_ult_movs.find_elements_by_tag_name('li')
        self.assertEqual(len(ult_movs), 1)
        self.assertIn(date.today(), ult_movs[0])
        self.assertIn('Carga de saldo inicial', ult_movs[0])
        self.assertIn('Efectivo', ult_movs[0])
        self.assertIn('985.50', ult_movs[0])

        # El importe cargado aparece en el campo saldo de la cuenta
        cuenta = self.esperar_elemento(
            'class_div_cuenta', criterio=By.CLASS_NAME)
        self.assertEqual(
            cuenta.find_element_by_class_name('class_saldo_cuenta').text,
            '985.50'
        )

        # El importe del movimiento también aparece sumado a activo y a saldo
        # general
        activo = self.esperar_elemento('id_importe_activo')
        saldo_gral = self.esperar_elemento('id_importe_saldo_gral')
        self.assertEqual(activo.text, '985.50')
        self.assertEqual(saldo_gral.text, '985.50')

