from django.test import TestCase
from django.urls import reverse


class TestHomePage(TestCase):

    def test_usa_template_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')


class TestCtaNueva(TestCase):

    def test_usa_template_cta_nueva(self):
        response = self.client.get(reverse('cta_nueva'))
        self.assertTemplateUsed(response, 'diario/cta_nueva.html')
