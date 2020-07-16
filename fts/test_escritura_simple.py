from datetime import date
from selenium.webdriver.common.keys import Keys

from .base import FunctionalTest


class TestVisitanteNuevo(FunctionalTest):

    def test_muestra_tabla_con_form_de_entrada(self):
        # Entro a la página web. El título es "Finanzas personales"
        self.assertIn('Finanzas Personales', self.browser.title)
        encabezado = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('Finanzas Personales', encabezado)

        # Debajo del encabezado hay una tabla con los siguientes encabezados:
        # Fecha, concepto, detalle, entrada, salida, total
        tablamovs = self.browser.find_element_by_id('id_table_movs')
        headers = tablamovs.find_elements_by_tag_name('th')
        for index, header in enumerate([
            'Fecha:',
            'Concepto:',
            'Detalle:',
            'Entrada:',
            'Salida:',
            'Total:',
        ]):
            self.assertEqual(header, headers[index].text)

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
        self.assertEqual(
            date.today().strftime("%d-%m-%Y"),
            fecha.get_attribute('value')
        )
        self.assertEqual('Concepto', concepto.get_attribute('placeholder'))
        self.assertEqual('Detalle', detalle.get_attribute('placeholder'))

        # Ingreso un movimiento con fecha, concepto, detalle, entrada y
        # salida.
        # La columna total se completa automáticamente con el cálculo del
        # saldo anterior.
        concepto.send_keys('Supermercado')
        detalle.send_keys('Arroz')
        salida.send_keys('250')
        self.browser.find_element_by_id('id_btn_submit').click()

        # Los datos ingresados pasan a formar parte del texto de la página,
        # y el formulario se desplaza un renglón hacia abajo.
        tablamovs = self.espera(
            lambda: self.browser.find_element_by_id('id_table_movs')
        )
        fecha = self.browser.find_element_by_id('id_td_fecha_01').text
        concepto = tablamovs.find_element_by_id('id_td_concepto_01').text
        detalle = tablamovs.find_element_by_id('id_td_detalle_01').text
        entrada = tablamovs.find_element_by_id('id_td_entrada_01').text
        salida = tablamovs.find_element_by_id('id_td_salida_01').text
        self.assertEqual(fecha, date.today().strftime('%d-%m-%Y'))
        self.assertEqual(concepto, 'Supermercado')
        self.assertEqual(detalle, 'Arroz')
        self.assertEqual(entrada, '')
        self.assertEqual(salida, '250.00')

        # Los campos del formulario se limpian y está listo para una nueva entrada

        filas = tablamovs.find_elements_by_tag_name('tr')
        celdas = filas[2].find_elements_by_tag_name('td')
        fecha = celdas[0].find_element_by_id('id_input_fecha')
        concepto = celdas[1].find_element_by_id('id_input_concepto')
        detalle = celdas[2].find_element_by_id('id_input_detalle')
        entrada = celdas[3].find_element_by_id('id_input_entrada')
        salida = celdas[4].find_element_by_id('id_input_salida')
        total = celdas[5].find_element_by_id('id_span_total').text

        self.assertEqual(
            date.today().strftime("%d-%m-%Y"),
            fecha.get_attribute('value')
        )
        self.assertEqual('Concepto', concepto.get_attribute('placeholder'))
        self.assertEqual('Detalle', detalle.get_attribute('placeholder'))
        self.assertEqual(concepto.get_attribute('value'), '')
        self.assertEqual(detalle.get_attribute('value'), '')
        self.assertEqual(entrada.get_attribute('value'), '')
        self.assertEqual(salida.get_attribute('value'), '')

        # La columna "Total" de la entrada anteriorse completa con el cálculo
        # de la diferencia entre entrada y salida.
        ###
        self.assertEqual(total, '250.00')



        # Validación y mensajes de error.

        # Al costado del total, un botón de Agregar Cuenta

        # Pulso el botón de agregar cuenta, se abre una página con
        # un formulario para agregar una nueva cuenta.

        # Completo el formulario y le doy OK. Regreso a la página principal.
        # Ésta tiene una nueva columna, cuyo encabezado es el nombre de la
        # cuenta.

