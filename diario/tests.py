from django.http import HttpRequest
from django.test import TestCase
from django.urls import resolve

from diario.views import home

class HomePageTest(TestCase):

    def test_url_raiz_resuelve_a_view_home(self):
        encontrado = resolve('/')
        self.assertEqual(encontrado.func, home)

    def test_home_page_devuelve_html_correcto(self):
        request = HttpRequest()
        response = home(request)
        html = response.content.decode('utf8')
        self.assertTrue(html.startswith('<html>'))
        self.assertIn('<title>Finanzas Personales - Movimientos diarios</title>', html)
        self.assertTrue(html.endswith('</html>'))

