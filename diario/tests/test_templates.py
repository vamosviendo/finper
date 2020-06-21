from datetime import date
from django.test import TestCase


class HomeTemplateTest(TestCase):

    def test_home_muestra_fecha_de_hoy(self):
        response = self.client.get('/')
        html = response.content.decode('utf8')
        cadena_fecha = date.today().strftime('%d-%m-%Y')
        self.assertInHTML(
            f'<input type="text" id="id_input_fecha" value="{cadena_fecha}"/>',
            html
        )
