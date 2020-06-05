from django.test import TestCase
from django.urls import resolve

from diario.views import home

class HomePageTest(TestCase):

    def test_url_raiz_resuelve_a_view_home(self):
        encontrado = resolve('/')
        self.assertEqual(encontrado.func, home)
