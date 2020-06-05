from selenium.webdriver.common.keys import Keys

from .base import FunctionalTest


class TestVisitanteNuevo(FunctionalTest):

    def test_puede_escribir_una_obra(self):
        # Entro a la página web. El título es Drama - Editor online de textos
        # dramáticos
        self.browser.get(self.live_server_url)
        self.assertIn('Title', self.browser.title)
        encabezado = self.browser.find_element_by_tag_name('h1')
        self.assertIn('Encabezado', encabezado)


