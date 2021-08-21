import datetime
from datetime import date
from pathlib import Path
from unittest import skip
from unittest.mock import patch, MagicMock

from django.http import HttpRequest
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from diario.models import Cuenta, CuentaAcumulativa, CuentaInteractiva, \
    Movimiento
from diario.views import cta_div_view
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

    def test_pasa_solo_cuentas_independientes_a_template(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        subctas = cta2.dividir_entre(
            {'nombre': 'Caja de ahorro', 'slug': 'bca', 'saldo': 0},
            {'nombre': 'Cuenta corriente', 'slug': 'bcc'},
        )
        cta2 = Cuenta.tomar(slug=cta2.slug)

        response = self.client.get(reverse('home'))

        self.assertIn(cta1, response.context['cuentas'])
        self.assertIn(cta2, response.context['cuentas'])
        for cta in subctas:
            self.assertNotIn(cta, response.context['cuentas'])

    def test_pasa_saldos_generales_a_template(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        Movimiento.crear(concepto='m1', importe=125, cta_entrada=cta1)
        Movimiento.crear(concepto='m3', importe=225, cta_entrada=cta2)

        response = self.client.get(reverse('home'))

        self.assertContains(response, '350.00')

    def test_considera_solo_cuentas_independientes_para_calcular_saldo_gral(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        Movimiento.crear(concepto='m1', importe=125, cta_entrada=cta1)
        Movimiento.crear(concepto='m3', importe=225, cta_entrada=cta2)
        subctas = cta2.dividir_entre(
            {'nombre': 'Caja de ahorro', 'slug': 'bca', 'saldo': 200},
            {'nombre': 'Cuenta corriente', 'slug': 'bcc'},
        )

        response = self.client.get(reverse('home'))

        self.assertEqual(response.context['saldo_gral'], 350)

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


class TestCtaDetalle(TestCase):

    def setUp(self):
        self.cta = Cuenta.crear('Efectivo', 'e')
        Movimiento.crear(
            concepto='a primer movimiento', importe=100, cta_entrada=self.cta)
        Movimiento.crear(
            concepto='b segundo movimiento', importe=30, cta_salida=self.cta)

    def test_usa_template_cta_detalle(self):
        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug]))
        self.assertTemplateUsed(response, 'diario/cta_detalle.html')

    def test_pasa_cuenta_a_template(self):
        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug]))
        self.assertEqual(
            response.context['cuenta'],
            Cuenta.tomar(polymorphic=False, slug=self.cta.slug)
        )
        self.assertContains(response, self.cta.nombre)

    def test_pasa_subcuentas_a_template(self):
        self.cta.dividir_entre(['ea', 'ea', 40], ['eb', 'eb'])
        self.cta = Cuenta.tomar(slug=self.cta.slug)
        self.assertTrue(self.cta.es_acumulativa)

        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug])
        )

        self.assertEqual(
            list(response.context['subcuentas']),
            list(self.cta.subcuentas.all())
        )

    def test_cuenta_interactiva_pasa_lista_vacia_en_subcuentas(self):
        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug])
        )
        self.assertEqual(list(response.context['subcuentas']), [])

    def test_pasa_movimientos_de_cuenta_a_template(self):
        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug]))
        self.assertEqual(
            list(response.context['movimientos']),
            list(self.cta.movs())
        )

    def test_pasa_movimientos_ordenados_por_fecha(self):
        m1 = Movimiento.tomar(concepto='a primer movimiento')
        m2 = Movimiento.tomar(concepto='b segundo movimiento')
        m3 = Movimiento.crear(
            fecha=date.today() - datetime.timedelta(days=2),
            concepto='c tercer movimiento',
            importe=30,
            cta_salida=self.cta
        )
        movs = [m3, m1, m2]

        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug]))

        self.assertEqual(list(response.context['movimientos']), movs)

    def test_pasa_movimientos_de_subcuentas(self):
        subcus = self.cta.dividir_entre(
            ['subcuenta1', 'sc1', 40], ['subcuenta2', 'sc2'])
        Movimiento.crear('c tercer movimiento', 30, cta_entrada=subcus[0])
        Movimiento.crear('d cuarto movimiento', 35, cta_salida=subcus[1])
        Movimiento.crear(
            'e quinto movimiento', 45,
            cta_entrada=subcus[0], cta_salida=subcus[1]
        )
        cuenta = CuentaAcumulativa.tomar(slug=self.cta.slug)

        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug]))

        self.assertEqual(
            list(response.context['movimientos']),
            list(cuenta.movs())
        )

    def test_integrativo_pasa_movs_de_cuenta_a_template(self):
        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug]))
        self.assertContains(response, 'a primer movimiento')
        self.assertContains(response, 'b segundo movimiento')


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
        self.assertEqual(cuenta_nueva.nombre, 'efectivo')

    def test_redirige_a_home_despues_de_POST(self):
        response = self.client.post(
            reverse('cta_nueva'),
            data={'nombre': 'Efectivo', 'slug': 'E'}
        )
        self.assertRedirects(response, reverse('home'))

    def test_solo_guarda_cuentas_con_post(self):
        # TODO ¿Retirar más adelante?
        self.client.get(reverse('cta_nueva'))
        self.assertEqual(Cuenta.cantidad(), 0)

    def test_cuentas_creadas_son_interactivas(self):
        self.client.post(
            reverse('cta_nueva'),
            data={'nombre': 'Efectivo', 'slug': 'E'}
        )
        cuenta_nueva = Cuenta.primere()
        self.assertEqual(cuenta_nueva.get_class(), CuentaInteractiva)


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
            ('nombro', 'slag')
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


def patch_save():
    mock = MagicMock()
    mock.return_value.save.return_value.get_absolute_url.return_value = 'stub'
    return mock


@patch('diario.views.FormSubcuentas', new_callable=patch_save)
class TestCtaDivFBV(TestCase):

    def setUp(self):
        self.cta = Cuenta.crear('Efectivo', 'e')
        Movimiento.crear(
            concepto='Ingreso de saldo', importe=250, cta_entrada=self.cta)
        self.request = HttpRequest()
        self.request.method = 'POST'
        self.request.POST['form-TOTAL_FORMS'] = 2
        self.request.POST['form-INITIAL_FORMS'] = 0
        self.request.POST['form-0-nombre'] = 'Billetera'
        self.request.POST['form-0-slug'] = 'eb'
        self.request.POST['form-0-saldo'] = 50
        self.request.POST['form-1-nombre'] = 'Cajón de arriba'
        self.request.POST['form-1-slug'] = 'ec'
        self.request.POST['form-1-saldo'] = 200

    def test_usa_template_cta_div_formset(self, falsoFormSubcuentas):
        response = self.client.get(reverse('cta_div', args=[self.cta.slug]))
        self.assertTemplateUsed(response, 'diario/cta_div_formset.html')

    @patch('diario.views.render')
    def test_muestra_form_subcuentas_al_acceder_a_pagina(
            self, falso_render, falsoFormSubcuentas):
        falso_form = falsoFormSubcuentas.return_value
        request = HttpRequest()
        request.method = 'GET'

        cta_div_view(request, slug=self.cta.slug)

        falsoFormSubcuentas.assert_called_once_with(cuenta=self.cta.slug)
        falso_render.assert_called_once_with(
            request,
            'diario/cta_div_formset.html',
            {'formset': falso_form}
        )

    def test_pasa_datos_post_y_cta_original_a_form_subcuentas(self, falsoFormSubcuentas):
        cta_div_view(self.request, slug=self.cta.slug)
        falsoFormSubcuentas.assert_called_with(
            data=self.request.POST,
            cuenta=self.cta.slug,
        )

    def test_guarda_form_si_los_datos_son_validos(self, falsoFormSubcuentas):
        falso_form = falsoFormSubcuentas.return_value
        falso_form.is_valid.return_value = True

        cta_div_view(self.request, slug=self.cta.slug)

        falso_form.save.assert_called_once()

    @patch('diario.views.redirect')
    def test_redirige_a_destino_si_el_form_es_valido(
            self, falso_redirect, falsoFormSubcuentas):
        falso_form = falsoFormSubcuentas.return_value
        falso_form.is_valid.return_value = True

        response = cta_div_view(self.request, slug=self.cta.slug)

        self.assertEqual(response, falso_redirect.return_value)
        falso_redirect.assert_called_once_with(falso_form.save.return_value)

    def test_no_guarda_form_si_los_datos_no_son_validos(self, falsoFormSubcuentas):
        falso_form = falsoFormSubcuentas.return_value
        falso_form.is_valid.return_value = False

        cta_div_view(self.request, slug=self.cta.slug)

        self.assertFalse(falso_form.save.called)

    @patch('diario.views.render')
    def test_vuelve_a_mostrar_template_y_form_con_form_no_valido(
            self, falso_render, falsoFormSubcuentas):
        falso_form = falsoFormSubcuentas.return_value
        falso_form.is_valid.return_value = False

        response = cta_div_view(self.request, slug=self.cta.slug)

        self.assertEqual(response, falso_render.return_value)
        falso_render.assert_called_once_with(
            self.request,
            'diario/cta_div_formset.html',
            {'formset': falso_form},
        )


@skip
@patch('diario.views.FormSubcuentas', new_callable=patch_save)
class TestCtaDiv(TestCase):

    def setUp(self):
        super().setUp()
        self.cta = Cuenta.crear('Efectivo', 'e')
        Movimiento.crear(
            concepto='Ingreso de saldo', importe=250, cta_entrada=self.cta)
        self.request = RequestFactory().post(
            reverse('cta_div', args=[self.cta]),
            data={
                'form-TOTAL_FORMS': 2,
                'form-INITIAL_FORMS': 0,
                # 'form-cuenta': self.cta.slug,
                'form-0-nombre': 'Billetera',
                'form-0-slug': 'ebil',
                'form-0-saldo': 50,
                'form-1-nombre': 'Cajón de arriba',
                'form-1-slug': 'ecaj',
                'form-1-saldo': 200,
            }
        )
        self.div_view = cta_div_view()

    def test_usa_template_cta_div_formset(self, falso_FormSubcuentas):
        response = self.client.get(reverse('cta_div', args=[self.cta.slug]))
        self.assertTemplateUsed(response, 'diario/cta_div_formset.html')

    def test_pasa_datos_POST_y_cta_original_a_form_subcuentas(self, falso_FormSubcuentas):
        self.div_view(self.request, slug=self.cta.slug)
        falso_FormSubcuentas.assert_called_once_with(
            # initial={},
            # prefix=None,
            data=self.request.POST,
            files=MultiValueDict(),
            cuenta=self.cta.slug,
        )

    def test_pasa_cta_original_a_form_subcuentas(self, falso_FormSubcuentas):
        self.div_view(self.request, slug=self.cta.slug)

    def test_guarda_form_si_los_datos_son_validos(self, falso_FormSubcuentas):
        falso_form = falso_FormSubcuentas.return_value
        falso_form.is_valid.return_value = True

        self.div_view(self.request, slug=self.cta.slug)

        falso_form.save.assert_called_once()

    def test_no_guarda_form_si_los_datos_no_son_validos(self, falso_FormSubcuentas):
        falso_form = falso_FormSubcuentas.return_value
        falso_form.is_valid.return_value = False

        self.div_view(self.request, slug=self.cta.slug)

        self.assertFalse(falso_form.save.called)

    @patch('diario.views.redirect')
    def test_redirige_a_pag_de_cuenta_con_form_valido(
            self, falso_redirect, falso_FormSubcuentas):
        falso_form = falso_FormSubcuentas.return_value
        falso_form.is_valid.return_value = True

        response = self.div_view(self.request, slug=self.cta.slug)

        self.assertEqual(response, falso_redirect.return_value)
        falso_redirect.assert_called_once_with(falso_form.save.return_value)

    @patch('diario.views.CtaDivView.response_class')
    def test_redibuja_template_con_formset_con_form_no_valido(
            self, falso_render, falso_FormSubcuentas):
        falso_form = falso_FormSubcuentas.return_value
        falso_form.is_valid.return_value = False

        response = self.div_view(self.request, slug=self.cta.slug)

        # Se llamó al mock y no a la función de la clase
        falso_render.assert_called_once()
        self.assertEqual(response, falso_render.return_value)

        # Se extraen los argumenos de llamado a falso_render
        llamada = falso_render.call_args
        args, kwargs = llamada

        self.assertEqual(kwargs['template'], ['diario/cta_div_formset.html'])
        self.assertEqual(kwargs['context']['form'], falso_form)


class TestCtaDivIntegration(TestCase):

    def setUp(self):
        self.cta = Cuenta.crear('Efectivo', 'e')
        Movimiento.crear(
            concepto='Ingreso de saldo', importe=250, cta_entrada=self.cta)
        self.response = self.client.post(
            reverse('cta_div', args=[self.cta.slug]),
            data={
                'form-TOTAL_FORMS': 2,
                'form-INITIAL_FORMS': 0,
                'form-0-nombre': 'Billetera',
                'form-0-slug': 'ebil',
                'form-0-saldo': 50,
                'form-1-nombre': 'Cajón de arriba',
                'form-1-slug': 'ecaj',
                'form-1-saldo': 200,
            },
        )

    def test_puede_dividir_cuenta_a_partir_de_POST(self):
        self.assertEqual(Cuenta.cantidad(), 3)
        self.assertEqual(
            len([x for x in Cuenta.todes() if x.es_interactiva]), 2)
        self.assertEqual(
            len([x for x in Cuenta.todes() if x.es_acumulativa]), 1)

    def test_redirige_a_pagina_de_cuenta(self):
        self.assertRedirects(
            self.response,
            reverse('cta_detalle', args=[self.cta.slug]),
        )


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
        self.assertEqual(mov_nuevo.cta_entrada.id, cuenta.id)

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
            data={
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

    def test_si_no_se_modifica_importe_no_cambia_saldo_cuentas(self):
        saldo = self.cuenta.saldo

        self.client.post(
            reverse('mov_mod', args=[self.mov.pk]),
            {
                'fecha': date.today(),
                'concepto': 'Saldo inicial',
                'importe': self.mov.importe,
                'cta_entrada': self.mov.cta_entrada.pk,
            }
        )
        self.cuenta.refresh_from_db()

        self.assertEqual(self.cuenta.saldo, saldo)


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

    @patch('diario.views.CuentaInteractiva.agregar_mov_correctivo')
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
