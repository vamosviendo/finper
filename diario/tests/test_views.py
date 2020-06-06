from django.test import TestCase


class HomeTest(TestCase):

    def test_usa_plantilla_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')
