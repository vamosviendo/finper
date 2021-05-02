from django.test import TestCase
from django.urls import reverse
from django.utils.datetime_safe import date

from diario.models import Cuenta, Movimiento


class TestHomePage(TestCase):

    def test_usa_template_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_pasa_cuentas_a_template(self):
        cta1 = Cuenta.objects.create(nombre='Efectivo', slug='E')
        cta2 = Cuenta.objects.create(nombre='Banco', slug='B')

        response = self.client.get(reverse('home'))

        self.assertIn(cta1, response.context.get('cuentas'))
        self.assertIn(cta2, response.context.get('cuentas'))

    def test_pasa_movimientos_a_template(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo', slug='E')
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
        cta1 = Cuenta.objects.create(nombre='Efectivo', slug='E')
        cta2 = Cuenta.objects.create(nombre='Banco', slug='B')
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
        cta1 = Cuenta.objects.create(nombre='Efectivo', slug='E', saldo=125)
        cta2 = Cuenta.objects.create(nombre='Banco', slug='B', saldo=225)

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
        self.client.post(
            reverse('cta_nueva'),
            data={'nombre': 'Efectivo', 'slug': 'E'}
        )
        self.assertEqual(Cuenta.objects.count(), 1)
        cuenta_nueva = Cuenta.objects.first()
        self.assertEqual(cuenta_nueva.nombre, 'Efectivo')

    def test_redirige_a_home_despues_de_POST(self):
        response = self.client.post(
            reverse('cta_nueva'),
            data={'nombre': 'Efectivo', 'slug': 'E'}
        )
        self.assertRedirects(response, reverse('home'))

    def test_solo_guarda_cuentas_con_post(self):
        # ¿Retirar más adelante?
        self.client.get(reverse('cta_nueva'))
        self.assertEqual(Cuenta.objects.count(), 0)


class TestCtaMod(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.crear(nombre='Nombre', slug='slug')

    def test_usa_template_cta_mod(self):
        response = self.client.get(reverse('cta_mod', args=[self.cuenta.slug]))
        self.assertTemplateUsed(response, 'diario/cta_mod.html')

    def test_post_puede_guardar_cambios_en_cuenta(self):
        self.client.post(
            reverse('cta_mod', args=[self.cuenta.slug]),
            data={'nombre': 'Nombro', 'slug': 'slag'}
        )
        self.cuenta.refresh_from_db()
        self.assertEqual(
            (self.cuenta.nombre, self.cuenta.slug),
            ('Nombro', 'SLAG')
        )

    def test_redirige_a_home_despues_de_post(self):
        response = self.client.post(
            reverse('cta_mod', args=[self.cuenta.slug]),
            data={'nombre': 'Nombro', 'slug': 'slag'}
        )
        self.assertRedirects(response, reverse('home'))


class TestCtaElim(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.crear('Efectivo', 'E')

    def test_get_usa_template_cuenta_confirm_delete(self):
        response = self.client.get(
            reverse('cta_elim', args=[self.cuenta.slug])
        )
        self.assertTemplateUsed(response, 'diario/cuenta_confirm_delete.html')

    def test_post_elimina_cuenta(self):
        self.client.post(
            reverse('cta_elim', args=[self.cuenta.slug])
        )
        self.assertEqual(Cuenta.objects.count(), 0)

    def test_redirige_a_home_despues_de_borrar(self):
        response = self.client.post(
            reverse('cta_elim', args=[self.cuenta.slug])
        )
        self.assertRedirects(response, reverse('home'))

    def test_muestra_mensaje_de_error_si_se_elimina_cuenta_con_saldo(self):
        Movimiento.objects.create(
            concepto='saldo', importe=100, cta_entrada=self.cuenta)
        response = self.client.get(
            reverse('cta_elim', args=[self.cuenta.slug])
        )
        self.assertContains(response, 'No se puede eliminar cuenta con saldo')


class TestMovNuevo(TestCase):

    def test_usa_template_mov_nuevo(self):
        response = self.client.get(reverse('mov_nuevo'))
        self.assertTemplateUsed(response, 'diario/mov_nuevo.html')

    def test_redirige_a_home_despues_de_POST(self):
        cuenta = Cuenta.objects.create(nombre='Efectivo', slug='E')
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
        cuenta = Cuenta.objects.create(nombre='Efectivo', slug='E')
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

    def test_no_guarda_movimientos_no_validos(self):
        self.client.post(
            reverse('mov_nuevo'),
            data={
                'fecha': date.today(),
                'concepto': 'entrada de efectivo',
                'importe': 100,
            }
        )
        self.assertEqual(Movimiento.objects.count(), 0)


class TestMovElim(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.objects.create(nombre='Efectivo', slug='E')
        self.mov = Movimiento.objects.create(
            concepto='saldo', importe=166, cta_entrada=self.cuenta)

    def test_usa_template_movimiento_confirm_delete(self):
        response = self.client.get(reverse('mov_elim', args=[self.mov.pk]))
        self.assertTemplateUsed(
            response, 'diario/movimiento_confirm_delete.html')

    def test_post_elimina_movimiento(self):
        self.client.post(reverse('mov_elim', args=[self.mov.pk]))
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_post_redirige_a_home(self):
        response = self.client.post(reverse('mov_elim', args=[self.mov.pk]))
        self.assertRedirects(response, reverse('home'))


class TestMovMod(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.objects.create(nombre='Efectivo', slug='E')
        self.mov = Movimiento.objects.create(
            concepto='saldo', importe=166, cta_entrada=self.cuenta)

    def test_usa_template_mov_mod(self):
        response = self.client.get(reverse('mov_mod', args=[self.mov.pk]))
        self.assertTemplateUsed(response, 'diario/mov_mod.html')

    def test_guarda_cambios_en_el_mov(self):
        self.client.post(
            reverse('mov_mod', args=[self.mov.pk]),
            {
                'fecha': date.today(),
                'concepto': 'Saldo inicial',
                'importe': self.mov.importe,
                'cta_entrada': self.mov.cta_entrada.pk,
            }
        )
        self.mov.refresh_from_db()
        self.assertEqual(self.mov.concepto, 'Saldo inicial')

    def test_redirige_a_home_despues_de_post(self):
        response = self.client.post(
            reverse('mov_mod', args=[self.mov.pk]),
            {
                'fecha': date.today(),
                'concepto': 'Saldo',
                'importe': self.mov.importe,
                'cta_entrada': self.mov.cta_entrada.pk,
            }
        )
        self.assertRedirects(response, reverse('home'))
