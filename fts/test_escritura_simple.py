from selenium.webdriver.common.keys import Keys

from .base import FunctionalTest


class TestVisitanteNuevo(FunctionalTest):

    def test_muestra_tabla_con_form_de_entrada(self):
        # Entro a la página web. El título es "Finanzas personales"
        self.browser.get(self.live_server_url)
        self.assertIn('Finanzas personales', self.browser.title)
        encabezado = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('Finanzas personales', encabezado)

        # Debajo del encabezado hay una tabla con los siguientes encabezados:
        # Fecha, concepto, detalle, entrada, salida, total

        # Debajo del encabezado, las celdas de la tabla están ocupadas por
        # campos de un formulario.
        # Ingreso un movimiento con fecha, concepto, detalle, entrada y salida.
        # La columna total se completa automáticamente con el cálculo del
        # saldo anterior.

        # Los datos ingresados pasan a formar parte del texto de la página,
        # y el formulario se desplaza una columna hacia abajo.




        # Al costado del total, un botón de Agregar Cuenta

        # Pulso el botón de agregar cuenta, se abre una página con
        # un formulario para agregar una nueva cuenta.

        # Completo el formulario y le doy OK. Regreso a la página principal.
        # Ésta tiene una nueva columna, cuyo encabezado es el nombre de la
        # cuenta.

