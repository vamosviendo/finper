from .base import FunctionalTest


class TestEstilo(FunctionalTest):

    def test_distribucion_y_estilo(self):

        encabezado = self.browser.find_element_by_tag_name('h1')
        fonts = encabezado.value_of_css_property('font-family')

        # Chequear que funciona bootstrap
        self.assertIn('apple', fonts)
        self.assertIn('Roboto', fonts)

        # Chequear que funcionan los estilos locales
        self.assertIn('nineteenthregular', fonts)

