from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.datetime_safe import date

from diario.models import Cuenta, Movimiento


class TestHomePage(TestCase):

    def test_usa_template_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_pasa_cuentas_a_template(self):
        cta1 = Cuenta.objects.create(nombre='Efectivo')
        cta2 = Cuenta.objects.create(nombre='Banco')

        response = self.client.get(reverse('home'))

        self.assertIn(cta1, response.context.get('cuentas'))
        self.assertIn(cta2, response.context.get('cuentas'))

    def test_pasa_movimientos_a_template(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo')
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='movimiento 1',
            importe=100,
            cta_entrada=cuenta
        )
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='movimiento 2',
            importe=50,
            cta_salida=cuenta
        )

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'movimiento 1')
        self.assertContains(response, 'movimiento 2')

    def test_pasa_saldo_de_cuentas_a_template(self):
        cta1 = Cuenta.objects.create(nombre='Efectivo')
        cta2 = Cuenta.objects.create(nombre='Banco')
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='movimiento 1',
            importe=100,
            cta_entrada=cta1
        )
        Movimiento.objects.create(
            fecha=date.today(),
            concepto='transferencia de fondos',
            importe=75,
            cta_entrada=cta2,
            cta_salida=cta1
        )

        response = self.client.get(reverse('home'))

        self.assertContains(response, '25.00')
        self.assertContains(response, '75.00')

    def test_pasa_saldos_generales_a_template(self):
        cta1 = Cuenta.objects.create(nombre='Efectivo', saldo=125)
        cta2 = Cuenta.objects.create(nombre='Banco', saldo=225)

        response = self.client.get(reverse('home'))

        self.assertContains(response, '350.00')

    def test_si_no_hay_movimientos_pasa_0_a_saldo_general(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['saldo_gral'], 0)

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

    def test_no_acepta_movimientos_no_validos(self):
        with self.assertRaises(ValidationError):
            self.client.post(
                reverse('mov_nuevo'),
                data={
                    'fecha': date.today(),
                    'concepto': 'entrada de efectivo',
                    'importe': 100,
                }
            )