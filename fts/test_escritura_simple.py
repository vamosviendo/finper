from datetime import date
from selenium.webdriver.common.keys import Keys

from .base import FunctionalTest


class TestVisitanteNuevo(FunctionalTest):

    def test_muestra_tabla_con_form_de_entrada(self):
        # Entro a la página web. El título es "Finanzas personales"
        self.browser.get(self.live_server_url)
        self.assertIn('Finanzas Personales', self.browser.title)
        encabezado = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('Finanzas Personales', encabezado)

        # Debajo del encabezado hay una tabla con los siguientes encabezados:
        # Fecha, concepto, detalle, entrada, salida, total
        tablamovs = self.browser.find_element_by_id('id_table_movs')
        headers = tablamovs.find_elements_by_tag_name('th')
        for index, header in enumerate(
                ['Fecha', 'Concepto', 'Detalle', 'Entrada', 'Salida', 'Total']
        ):
            print(index, header)
            self.assertEqual(header, headers[index])

        # Debajo del encabezado, las celdas de la tabla están ocupadas por
        # campos de un formulario.
        filas = tablamovs.find_elements_by_tag_name('tr')
        celdas = filas[1].find_elements_by_tag_name('td')
        fecha = celdas[0].find_element_by_id('id_input_fecha')
        concepto = celdas[1].find_element_by_id('id_input_concepto')
        detalle = celdas[2].find_element_by_id('id_input_detalle')
        entrada = celdas[3].find_element_by_id('id_input_entrada')
        salida = celdas[4].find_element_by_id('id_input_salida')
        total = celdas[5].find_element_by_id('id_span_total').text

        # Algunos de los campos del formulario vienen con valores por defecto.
        # Los que no, tienen un placeholder.
        # (Comprobar valores por defecto, placeholders y que no haya
        # ningún campo que no cumpla alguna de estas dos opciones).
        print('Fecha por defecto:', fecha.get_attribute('value'))
        self.assertEqual(date.today(), fecha.get_attribute('value'))
        self.assertEqual('Concepto', concepto.get_attribute('placeholder'))
        self.assertEqual('Detalle', detalle.get_attribute('placeholder'))
        self.assertEqual('Entrada', entrada.get_attribute('value'))
        self.assertEqual('Salida', salida.get_attribute('value'))

        # Ingreso un movimiento con fecha, concepto, detalle, entrada y salida.
        # La columna total se completa automáticamente con el cálculo del
        # saldo anterior.
        fecha.send_keys(Keys.TAB)
        concepto.send_keys('Supermercado')
        concepto.send_keys(Keys.TAB)
        detalle.send_keys('Arroz')
        detalle.send_keys(Keys.TAB)
        entrada.send_keys(Keys.TAB)
        salida.send_keys('250')
        salida.send_keys(Keys.ENTER)
        self.assertEqual(total, '250.00')

        # Los datos ingresados pasan a formar parte del texto de la página,
        # y el formulario se desplaza una columna hacia abajo.
        fecha = celdas[0].find_element_by_id('id_span_fecha').text
        concepto = celdas[1].find_element_by_id('id_span_concepto').text
        detalle = celdas[2].find_element_by_id('id_span_detalle').text
        entrada = celdas[3].find_element_by_id('id_span_entrada').text
        salida = celdas[4].find_element_by_id('id_span_salida').text
        self.assertEqual(fecha, date.today())
        self.assertEqual(concepto, 'Supermercado')
        self.assertEqual(detalle, 'Arroz')
        self.assertIsNone(entrada)
        self.assertEqual(salida, '250.00')
        celdas = filas[2].find_elements_by_tag_name('td')
        fecha = celdas[0].find_element_by_id('id_input_fecha')
        concepto = celdas[1].find_element_by_id('id_input_concepto')
        detalle = celdas[2].find_element_by_id('id_input_detalle')
        entrada = celdas[3].find_element_by_id('id_input_entrada')
        salida = celdas[4].find_element_by_id('id_input_salida')
        total = celdas[5].find_element_by_id('id_span_total').text



        # Al costado del total, un botón de Agregar Cuenta

        # Pulso el botón de agregar cuenta, se abre una página con
        # un formulario para agregar una nueva cuenta.

        # Completo el formulario y le doy OK. Regreso a la página principal.
        # Ésta tiene una nueva columna, cuyo encabezado es el nombre de la
        # cuenta.

