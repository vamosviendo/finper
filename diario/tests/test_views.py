from django.test import TestCase
from django.urls import reverse

from diario.models import Cuenta


class TestHomePage(TestCase):

    def test_usa_template_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_muestra_todas_las_cuentas(self):
        Cuenta.objects.create(nombre='Efectivo')
        Cuenta.objects.create(nombre='Caja de ahorro')

        response = self.client.get(reverse('home'))

        self.assertIn('Efectivo', response.content.decode())
        self.assertIn('Caja de ahorro', response.content.decode())


class TestCtaNueva(TestCase):

    def test_usa_template_cta_nueva(self):
        response = self.client.get(reverse('cta_nueva'))
        self.assertTemplateUsed(response, 'diario/cta_nueva.html')

    def test_puede_guardar_cuenta_nueva(self):
        self.client.post(reverse('cta_nueva'), data={'nombre': 'Efectivo'})
        self.assertEqual(Cuenta.objects.count(), 1)
        cuenta_nueva = Cuenta.objects.first()
        self.assertEqual(cuenta_nueva.nombre, 'Efectivo')

    def test_redirige_a_home_despues_de_POST(self):
        response = self.client.post(
            reverse('cta_nueva'),
            data={'nombre': 'Efectivo'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], reverse('home'))

    def test_solo_guarda_cuentas_con_post(self):
        # ¿Retirar más adelante?
        self.client.get(reverse('cta_nueva'))
        self.assertEqual(Cuenta.objects.count(), 0)
