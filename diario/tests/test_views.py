from django.test import TestCase

from diario.forms import FormMovimiento


class HomeTest(TestCase):

    def test_usa_plantilla_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_usa_form_movimiento(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], FormMovimiento)
        pass

    def test_calcula_total_movimiento(self):
        pass

    def test_muestra_total_movimiento(self):
        pass

    def test_puede_guardar_un_movimiento(self):
        # (puede guardar un request.POST)
        pass

    def test_POST_redirige_a_home(self):
        pass

    def test_muestra_movimientos_anteriores(self):
        pass

    def test_entrada_invalida_no_guarda_movimiento(self):
        pass

    def test_entrada_invalida_muestra_plantilla_home(self):
        pass

    def test_entrada_invalida_pasa_form_a_plantilla(self):
        pass

    def test_entrada_invalida_muestra_mensajes_de_error(self):
        pass

    def test_distintos_tipos_de_error(self):
        pass

    def test_muestra_movimientos_anteriores(self):
        pass

    def test_calcula_total_acumulado(self):
        pass