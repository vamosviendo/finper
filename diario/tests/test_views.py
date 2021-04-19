from django.test import TestCase
from django.urls import reverse
from django.utils.datetime_safe import date

from diario.models import Cuenta, Movimiento


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
        self.assertRedirects(response, reverse('home'))

    def test_solo_guarda_cuentas_con_post(self):
        # ¿Retirar más adelante?
        self.client.get(reverse('cta_nueva'))
        self.assertEqual(Cuenta.objects.count(), 0)


class TestMovNuevo(TestCase):

    def test_usa_template_mov_nuevo(self):
        response = self.client.get(reverse('mov_nuevo'))
        self.assertTemplateUsed(response, 'diario/mov_nuevo.html')

    def test_pasa_todas_las_cuentas_a_template(self):
        Cuenta.objects.create(nombre='cuenta 1')
        Cuenta.objects.create(nombre='cuenta 2')
        response = self.client.get(reverse('mov_nuevo'))
        self.assertEqual(
            list(Cuenta.objects.all()),
            list(response.context['cuentas'])
        )

    def test_redirige_a_home_despues_de_POST(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        response = self.client.post(
            reverse('mov_nuevo'),
            data={
                'fecha': date.today(),
                'concepto': 'entrada de efectivo',
                'importe': 100,
                'cta_entrada': cuenta.id,
            }
        )
        self.assertRedirects(response, reverse('home'))

    def test_puede_guardar_movimiento_nuevo(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        self.client.post(
            reverse('mov_nuevo'),
            data={
                'fecha': date.today(),
                'concepto': 'entrada de efectivo',
                'importe': 100,
                'cta_entrada': cuenta.id
            }
        )
        self.assertEqual(Movimiento.objects.count(), 1)
        mov_nuevo = Movimiento.objects.first()
        self.assertEqual(mov_nuevo.fecha, date.today())
        self.assertEqual(mov_nuevo.concepto, 'entrada de efectivo')
        self.assertEqual(mov_nuevo.importe, 100)
        self.assertEqual(mov_nuevo.cta_entrada, cuenta)
