from django.test import TestCase
from django.urls import resolve

from diario.views import home


class TestHomePage(TestCase):

    def test_resuelve_a_view_home(self):
        found = resolve('/')
        self.assertEqual(found.func, home)

    def test_usa_template_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')