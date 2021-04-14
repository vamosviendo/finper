from django.test import TestCase
from django.urls import resolve

from diario.views import home


class TestHomePage(TestCase):

    def test_resuelve_a_view_home(self):
        found = resolve('/')
        self.assertEqual(found.func, home)
