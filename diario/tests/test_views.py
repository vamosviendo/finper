from django.http import HttpRequest
from django.test import TestCase
from django.urls import resolve

from diario.views import home


class HomePageTest(TestCase):

    def test_usa_plantilla_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

