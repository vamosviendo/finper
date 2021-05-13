import datetime
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from diario.models import Cuenta, Movimiento
from utils.funciones.archivos import fijar_mtime


class TestHomePage(TestCase):

    def test_usa_template_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_pasa_cuentas_a_template(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')

        response = self.client.get(reverse('home'))

        self.assertIn(cta1, response.context.get('cuentas'))
        self.assertIn(cta2, response.context.get('cuentas'))

    def test_pasa_movimientos_a_template(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        Movimiento.crear(
            fecha=date.today(),
            concepto='movimiento 1',
            importe=100,
            cta_entrada=cuenta
        )
        Movimiento.crear(
            fecha=date.today(),
            concepto='movimiento 2',
            importe=50,
            cta_salida=cuenta
        )

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'movimiento 1')
        self.assertContains(response, 'movimiento 2')

    def test_pasa_saldo_de_cuentas_a_template(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        Movimiento.crear(
            fecha=date.today(),
            concepto='movimiento 1',
            importe=100,
            cta_entrada=cta1
        )
        Movimiento.crear(
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
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        Movimiento.crear(concepto='m1', importe=125, cta_entrada=cta1)
        Movimiento.crear(concepto='m3', importe=225, cta_entrada=cta2)

        response = self.client.get(reverse('home'))

        self.assertContains(response, '350.00')

    def test_si_no_hay_movimientos_pasa_0_a_saldo_general(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['saldo_gral'], 0)


@patch('diario.views.verificar_saldos')
class TestHomePageVerificarSaldo(TestCase):

    def setUp(self):
        super().setUp()
        self.fecha = datetime.date(2021, 4, 4)
        self.hora = datetime.datetime(2021, 4, 4)

        # Falsificar datetime.date today (no se puede con @patch)
        class FalsaFecha(datetime.date):
            @classmethod
            def today(cls):
                return self.fecha

        class FalsaHora(datetime.datetime):
            @classmethod
            def now(cls):
                return self.hora

        self.patcherf = patch('datetime.date', FalsaFecha)
        self.patcherh = patch('datetime.datetime', FalsaHora)
        self.patcherf.start()
        self.patcherh.start()

        # Preservar marca de fecha
        self.hoy = Path('hoy.mark')
        self.ayer = self.hoy.rename('ayer.mark')
        self.hoy.touch()
        fijar_mtime(self.hoy, datetime.datetime(2021, 4, 4))

    def tearDown(self):
        self.patcherf.stop()
        self.patcherh.stop()

        # Recuperar marca de fecha
        self.hoy.unlink()
        self.ayer.rename('hoy.mark')
        super().tearDown()

    def test_verifica_saldo_de_cuentas_si_cambia_la_fecha(
            self, mock_verificar_saldos):

        self.fecha = datetime.date(2021, 4, 5)
        self.client.get(reverse('home'))
        mock_verificar_saldos.assert_called_once()

    def test_no_verifica_saldo_de_cuentas_si_no_cambia_la_fecha(
            self, mock_verificar_saldos):

        self.client.get(reverse('home'))

        mock_verificar_saldos.assert_not_called()

    @patch('diario.views.Path.touch')
    def test_actualiza_fecha_despues_de_verificar_saldos(
            self, mock_touch, mock_verificar_saldos):
        self.fecha = datetime.date(2021, 4, 5)
        self.hora = datetime.datetime(2021, 4, 5)

        self.client.get(reverse('home'))
        mock_touch.assert_called_once()

    def test_si_saldo_no_coincide_redirige_a_corregir_saldo_con_lista_de_ctas_erroneas(
            self, mock_verificar_saldos):
        cta1 = Cuenta.crear('Efectivo', 'E')
        cta2 = Cuenta.crear('Banco', 'B')
        mock_verificar_saldos.return_value = [cta1, cta2, ]
        self.fecha = datetime.date(2021, 4, 5)
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('corregir_saldo')}?ctas=e!b")


class TestCtaNueva(TestCase):

    def test_usa_template_cta_form(self):
        response = self.client.get(reverse('cta_nueva'))
        self.assertTemplateUsed(response, 'diario/cta_form.html')

    def test_puede_guardar_cuenta_nueva(self):
        self.client.post(
            reverse('cta_nueva'),
            data={'nombre': 'Efectivo', 'slug': 'E'}
        )
        self.assertEqual(Cuenta.cantidad(), 1)
        cuenta_nueva = Cuenta.primere()
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
        self.assertEqual(Cuenta.cantidad(), 0)


class TestCtaMod(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.crear(nombre='Nombre', slug='slug')

    def test_usa_template_cta_form(self):
        response = self.client.get(reverse('cta_mod', args=[self.cuenta.slug]))
        self.assertTemplateUsed(response, 'diario/cta_form.html')

    def test_post_puede_guardar_cambios_en_cuenta(self):
        self.client.post(
            reverse('cta_mod', args=[self.cuenta.slug]),
            data={'nombre': 'Nombro', 'slug': 'Slag'}
        )
        self.cuenta.refresh_from_db()
        self.assertEqual(
            (self.cuenta.nombre, self.cuenta.slug),
            ('Nombro', 'slag')
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
        self.assertEqual(Cuenta.cantidad(), 0)

    def test_redirige_a_home_despues_de_borrar(self):
        response = self.client.post(
            reverse('cta_elim', args=[self.cuenta.slug])
        )
        self.assertRedirects(response, reverse('home'))

    def test_muestra_mensaje_de_error_si_se_elimina_cuenta_con_saldo(self):
        Movimiento.crear(
            concepto='saldo', importe=100, cta_entrada=self.cuenta)
        response = self.client.get(
            reverse('cta_elim', args=[self.cuenta.slug])
        )
        self.assertContains(response, 'No se puede eliminar cuenta con saldo')


class TestMovNuevo(TestCase):

    def test_usa_template_mov_form(self):
        response = self.client.get(reverse('mov_nuevo'))
        self.assertTemplateUsed(response, 'diario/mov_form.html')

    def test_redirige_a_home_despues_de_POST(self):
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
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
        cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.client.post(
            reverse('mov_nuevo'),
            data={
                'fecha': date.today(),
                'concepto': 'entrada de efectivo',
                'importe': 100,
                'cta_entrada': cuenta.id
            }
        )
        self.assertEqual(Movimiento.cantidad(), 1)
        mov_nuevo = Movimiento.primere()
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
        self.assertEqual(Movimiento.cantidad(), 0)


class TestMovElim(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.mov = Movimiento.crear(
            concepto='saldo', importe=166, cta_entrada=self.cuenta)

    def test_usa_template_movimiento_confirm_delete(self):
        response = self.client.get(reverse('mov_elim', args=[self.mov.pk]))
        self.assertTemplateUsed(
            response, 'diario/movimiento_confirm_delete.html')

    def test_post_elimina_movimiento(self):
        self.client.post(reverse('mov_elim', args=[self.mov.pk]))
        self.assertEqual(Movimiento.cantidad(), 0)

    def test_post_redirige_a_home(self):
        response = self.client.post(reverse('mov_elim', args=[self.mov.pk]))
        self.assertRedirects(response, reverse('home'))


class TestMovMod(TestCase):

    def setUp(self):
        super().setUp()
        self.cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.mov = Movimiento.crear(
            concepto='saldo', importe=166, cta_entrada=self.cuenta)

    def test_usa_template_mov_form(self):
        response = self.client.get(reverse('mov_mod', args=[self.mov.pk]))
        self.assertTemplateUsed(response, 'diario/mov_form.html')

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


class TestCorregirSaldo(TestCase):

    def setUp(self):
        super().setUp()
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        self.cta2 = Cuenta.crear('Banco', 'B')
        self.full_url = f"{reverse('corregir_saldo')}?ctas=e!b"

    def test_usa_template_corregir_saldo(self):
        response = self.client.get(self.full_url)
        self.assertTemplateUsed(response, 'diario/corregir_saldo.html')

    def test_redirige_a_home_si_no_recibe_querystring_o_con_querystring_mal_formada(self):
        url1 = reverse('corregir_saldo')
        url2 = f"{reverse('corregir_saldo')}?ctas="
        url3 = f"{reverse('corregir_saldo')}?ctas=a"
        url4 = f"{reverse('corregir_saldo')}?cuculo=2"
        self.assertRedirects(self.client.get(url1), reverse('home'))
        self.assertRedirects(self.client.get(url2), reverse('home'))
        self.assertRedirects(self.client.get(url3), reverse('home'))
        self.assertRedirects(self.client.get(url4), reverse('home'))

    def test_pasa_lista_de_cuentas_erroneas_a_template(self):
        response = self.client.get(self.full_url)
        self.assertEqual(
            response.context['ctas_erroneas'], [self.cta1, self.cta2, ])


class TestModificarSaldo(TestCase):

    def setUp(self):
        super().setUp()
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        self.cta2 = Cuenta.crear('Banco', 'B')
        self.full_url = f"{reverse('modificar_saldo', args=[self.cta1.slug])}" \
                        f"?ctas=e!b"

    def test_redirige_a_corregir_saldo_con_ctas_erroneas_menos_la_corregida(self):
        response = self.client.get(self.full_url)
        self.assertRedirects(response, f"{reverse('corregir_saldo')}?ctas=b")

    def test_redirige_a_home_si_es_la_unica_cuenta_erronea(self):
        response = self.client.get(
            f"{reverse('modificar_saldo', args=[self.cta2.slug])}"
            f"?ctas=b"
        )
        self.assertRedirects(response, f"{reverse('home')}")

    @patch('diario.views.Cuenta.corregir_saldo')
    def test_corrige_saldo_de_cuenta(self, mock_cta_corregir_saldo):
        self.client.get(self.full_url)
        mock_cta_corregir_saldo.assert_called_once()


class TestAgregarMovimiento(TestCase):

    def setUp(self):
        super().setUp()
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        self.cta2 = Cuenta.crear('Banco', 'B')
        self.full_url = \
            f"{reverse('agregar_movimiento', args=[self.cta2.slug])}" \
            f"?ctas=e!b"

    def test_redirige_a_corregir_saldo_con_ctas_erroneas_menos_la_corregida(self):
        response = self.client.get(self.full_url)
        self.assertRedirects(response, f"{reverse('corregir_saldo')}?ctas=e")

    def test_redirige_a_home_si_es_la_unica_cuenta_erronea(self):
        response = self.client.get(
            f"{reverse('agregar_movimiento', args=[self.cta2.slug])}"
            f"?ctas=b"
        )
        self.assertRedirects(response, f"{reverse('home')}")

    @patch('diario.views.Cuenta.agregar_mov_correctivo')
    def test_agrega_movimiento_para_coincidir_con_saldo(
            self, mock_cta_agregar_mov):
        self.client.get(self.full_url)
        mock_cta_agregar_mov.assert_called_once()

    def test_integrativo_agrega_movimiento_para_coincidir_con_saldo(self):
        Movimiento.crear(concepto='mov', importe=100, cta_entrada=self.cta2)
        cant_movs = self.cta1.cantidad_movs()
        self.cta2.saldo = 135

        self.client.get(self.full_url)

        self.assertEqual(self.cta2.cantidad_movs(), cant_movs+1)
        self.assertEqual(self.cta2.saldo, 135)
