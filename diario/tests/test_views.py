import datetime
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from diario.forms import FormCuenta, FormCrearSubcuenta
from diario.models import Cuenta, CuentaAcumulativa, CuentaInteractiva, \
    Movimiento, Titular
from diario.views import cta_div_view
from utils.archivos import fijar_mtime
from utils.helpers_tests import dividir_en_dos_subcuentas
from utils.iterables import dict2querydict


class TestTitularNuevo(TestCase):

    def test_usa_template_tit_form(self):
        response = self.client.get(reverse('tit_nuevo'))
        self.assertTemplateUsed(response, 'diario/tit_form.html')

    def test_post_redirige_a_home(self):
        Cuenta.crear(nombre='cuenta', slug='cta')
        response = self.client.post(
            reverse('tit_nuevo'),
            data={'titname': 'tito', 'nombre': 'Tito Gómez'})
        self.assertRedirects(response, reverse('home'))


class TestTitularDetalle(TestCase):

    def setUp(self):
        self.tit = Titular.crear(titname='tito', nombre='Tito Gómez')

    def test_usa_template_tit_detalle(self):
        response = self.client.get(reverse('tit_detalle', args=[self.tit.pk]))
        self.assertTemplateUsed(response, 'diario/tit_detalle.html')

    def test_pasa_cuentas_del_titular_al_template(self):
        cuenta1 = Cuenta.crear(nombre='cuenta1', slug='cta1', titular=self.tit)
        cuenta2 = Cuenta.crear(nombre='cuenta2', slug='cta2', titular=self.tit)
        cuenta3 = Cuenta.crear(nombre='cuenta3', slug='cta3')

        response = self.client.get(reverse('tit_detalle', args=[self.tit.pk]))

        self.assertEqual(
            list(response.context['subcuentas']),
            [cuenta1, cuenta2]
        )

    @patch('diario.views.Titular.patrimonio', new_callable=PropertyMock)
    def test_pasa_patrimonio_del_titular_al_template(self, mock_patrimonio):
        mock_patrimonio.return_value = 250

        response = self.client.get(reverse('tit_detalle', args=[self.tit.pk]))

        self.assertEqual(response.context['saldo_pag'], 250)

    @patch('diario.views.Titular.movimientos')
    def test_pasa_movimientos_relacionados_con_cuentas_del_titular_al_template(self, mock_movimientos):
        cuenta1 = Cuenta.crear(nombre='cuenta1', slug='cta1', titular=self.tit)
        cuenta2 = Cuenta.crear(nombre='cuenta2', slug='cta2')
        mov1 = Movimiento.crear('Movimiento 1', 120, cuenta1)
        mov2 = Movimiento.crear('Movimiento 2', 65, None, cuenta2)
        mov3 = Movimiento.crear('Movimiento 3', 35, cuenta1, cuenta2)

        mock_movimientos.return_value = [mov1, mov3]

        response = self.client.get(reverse('tit_detalle', args=[self.tit.pk]))

        self.assertIn('movimientos', response.context.keys())
        self.assertEqual(list(response.context['movimientos']), [mov1, mov3])


class TestTitularElim(TestCase):

    def setUp(self):
        super().setUp()
        self.titular = Titular.crear(titname='Tito')
        self.cuenta = Cuenta.crear('cuenta', 'cta')

    def test_get_usa_template_titular_confirm_delete(self):
        response = self.client.get(
            reverse('tit_elim', args=[self.titular.pk])
        )
        self.assertTemplateUsed(response, 'diario/titular_confirm_delete.html')

    def test_redirige_a_home_despues_de_borrar(self):
        response = self.client.post(
            reverse('tit_elim', args=[self.titular.pk])
        )
        self.assertRedirects(response, reverse('home'))

    @patch('diario.views.Titular.delete')
    def test_post_elimina_titular(self, mock_delete):
        self.client.post(
            reverse('tit_elim', args=[self.titular.pk])
        )
        mock_delete.assert_called_once()


class TestHomePage(TestCase):

    def setUp(self):
        super().setUp()
        Titular.crear(titname='juan')
        Cuenta.crear(nombre='cuenta', slug='cta')

    def test_usa_template_home(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'diario/home.html')

    def test_pasa_titulares_a_template(self):
        tit1 = Titular.crear(titname='titu')
        tit2 = Titular.crear(titname='titi')

        response = self.client.get(reverse('home'))

        self.assertIn(tit1, response.context.get('titulares'))
        self.assertIn(tit2, response.context.get('titulares'))

    def test_pasa_cuentas_a_template(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')

        response = self.client.get(reverse('home'))

        self.assertIn(cta1, response.context.get('subcuentas'))
        self.assertIn(cta2, response.context.get('subcuentas'))

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

        self.assertContains(response, '25,00')
        self.assertContains(response, '75,00')

    def test_pasa_solo_cuentas_independientes_a_template(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        subctas = cta2.dividir_entre(
            {'nombre': 'Caja de ahorro', 'slug': 'bca', 'saldo': 0},
            {'nombre': 'Cuenta corriente', 'slug': 'bcc'},
        )
        cta2 = Cuenta.tomar(slug=cta2.slug)

        response = self.client.get(reverse('home'))

        self.assertIn(cta1, response.context['subcuentas'])
        self.assertIn(cta2, response.context['subcuentas'])
        for cta in subctas:
            self.assertNotIn(cta, response.context['subcuentas'])

    def test_pasa_saldos_generales_a_template(self):
        cta1 = Cuenta.crear(nombre='Efectivo', slug='E')
        cta2 = Cuenta.crear(nombre='Banco', slug='B')
        Movimiento.crear(concepto='m1', importe=125, cta_entrada=cta1)
        Movimiento.crear(concepto='m3', importe=225, cta_entrada=cta2)

        response = self.client.get(reverse('home'))

        self.assertContains(response, '350,00')

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

    def test_si_no_hay_titulares_redirige_a_crear_titular(self):
        Titular.todes().delete()

        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('tit_nuevo'))

    def test_si_no_hay_cuentas_redirige_a_crear_cuenta(self):
        for cta in Cuenta.todes():
            cta.delete()

        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('cta_nueva'))

    def test_si_no_hay_movimientos_pasa_0_a_saldo_general(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['saldo_gral'], 0)


class TestHomePageVerificarSaldo(TestCase):

    def setUp(self):
        super().setUp()
        Titular.crear(titname='tito')
        Cuenta.crear(nombre='cuenta', slug='cta')

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

    def test_verifica_saldo_de_cuentas_si_cambia_la_fecha(self):

        self.fecha = datetime.date(2021, 4, 5)
        response = self.client.get(reverse('home'))
        self.assertRedirects(
            response, reverse('verificar_saldos'), target_status_code=302)

    @patch('diario.views.Path.touch')
    def test_actualiza_fecha_despues_de_verificar_saldos(self, mock_touch):
        self.fecha = datetime.date(2021, 4, 5)
        self.hora = datetime.datetime(2021, 4, 5)

        self.client.get(reverse('home'))
        mock_touch.assert_called_once()


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

    def test_cuenta_interactiva_pasa_titular_a_template(self):
        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug]))
        self.assertEqual(response.context['titulares'], [self.cta.titular])

    @patch('diario.views.CuentaAcumulativa.titulares', new_callable=PropertyMock)
    def test_cuenta_acumulativa_pasa_titulares_de_subcuentas_a_template(
            self, falso_titulares):
        tit1 = Titular.crear(titname='juan', nombre='Juan Gómez')
        tit2 = Titular.crear(titname='tita', nombre='Tita Pérez')

        self.cta.dividir_entre(['ea', 'ea', 40], ['eb', 'eb'])
        self.cta = Cuenta.tomar(slug=self.cta.slug)

        falso_titulares.return_value = [tit1, tit2]
        response = self.client.get(
            reverse('cta_detalle', args=[self.cta.slug]))
        falso_titulares.assert_called_once()
        self.assertEqual(response.context['titulares'], [tit1, tit2])

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

    def setUp(self):
        super().setUp()
        Titular.crear(titname='tito')

    def test_si_no_hay_titulares_redirige_a_crear_titular(self):
        Titular.todes().delete()
        response = self.client.get(reverse('cta_nueva'))
        self.assertRedirects(response, reverse('tit_nuevo'))

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
        self.tit = Titular.crear(titname='tito')
        self.cuenta = Cuenta.crear(nombre='Nombre', slug='slug')

    def test_usa_template_cta_form(self):
        response = self.client.get(
            reverse('cta_mod', args=[self.cuenta.slug]))
        self.assertTemplateUsed(response, 'diario/cta_form.html')

    def test_usa_form_cuenta(self):
        response = self.client.get(
            reverse('cta_mod', args=[self.cuenta.slug]),
            data={'nombre': 'Nombro', 'slug': 'Slag'}
        )
        self.assertIsInstance(response.context['form'], FormCuenta)

    def test_no_permite_modificar_titular(self):
        response = self.client.get(
            reverse('cta_mod', args=[self.cuenta.slug])
        )
        self.assertTrue(
            response.context['form'].fields['titular'].disabled)

    def test_post_puede_guardar_cambios_en_cuenta_interactiva(self):
        self.client.post(
            reverse('cta_mod', args=[self.cuenta.slug]),
            data={'nombre': 'Nombro', 'slug': 'Slag'}
        )
        self.cuenta.refresh_from_db()
        self.assertEqual(
            (self.cuenta.nombre, self.cuenta.slug),
            ('nombro', 'slag')
        )

    def test_post_puede_guardar_cambios_en_cuenta_acumulativa(self):
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)
        self.client.post(
            reverse('cta_mod', args=[self.cuenta.slug]),
            data={'nombre': 'Cuenta', 'slug': 'cta'}
        )
        self.cuenta.refresh_from_db()
        self.assertEqual(
            (self.cuenta.nombre, self.cuenta.slug),
            ('cuenta', 'cta')
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
        Titular.crear(titname='tito')
        Cuenta.crear('cuenta', 'cta')
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
        self.assertEqual(Cuenta.cantidad(), 1)

    def test_redirige_a_home_despues_de_borrar(self):
        response = self.client.post(
            reverse('cta_elim', args=[self.cuenta.slug])
        )
        self.assertRedirects(response, reverse('home'))

    def test_redirige_a_crear_cuenta_si_no_hay_mas_cuentas(self):
        Cuenta.tomar(slug='cta').delete()
        response = self.client.post(
            reverse('cta_elim', args=[self.cuenta.slug])
        )
        self.assertRedirects(response, reverse('cta_nueva'))

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
class TestCtaDiv(TestCase):

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


class TestCtaAgregarSubc(TestCase):

    def setUp(self):
        self.cuenta = dividir_en_dos_subcuentas(Cuenta.crear('cuenta', 'cta'))
        self.datadict = {'nombre': 'subcuenta_3', 'slug': 'sc3'}

    def test_usa_template_agregar_subcuenta(self):
        response = self.client.get(
            reverse('cta_agregar_subc', args=[self.cuenta.slug]))
        self.assertTemplateUsed(response, 'diario/cta_agregar_subc.html')

    @patch('diario.views.FormCrearSubcuenta', new_callable=patch_save)
    def test_GET_muestra_form_FormCrearSubcuenta_vacio(self, falso_FormCrearSubcuenta):
        self.client.get(
            reverse('cta_agregar_subc', args=[self.cuenta.slug]))
        falso_FormCrearSubcuenta.assert_called_once_with(
            cuenta=self.cuenta.slug)

    @patch('diario.views.FormCrearSubcuenta', new_callable=patch_save)
    def test_POST_pasa_datos_y_cta_original_a_form_subcuentas(self, falso_FormCrearSubcuenta):
        self.client.post(
            reverse('cta_agregar_subc', args=[self.cuenta.slug]),
            data=self.datadict
        )

        falso_FormCrearSubcuenta.assert_called_once_with(
            data=dict2querydict(self.datadict),
            cuenta=self.cuenta.slug,
        )

    @patch('diario.views.FormCrearSubcuenta', new_callable=patch_save)
    def test_guarda_form_con_datos_validos(self, falso_FormCrearSubcuenta):
        falso_form = falso_FormCrearSubcuenta.return_value
        falso_form.is_valid.return_value = True

        self.client.post(
            reverse('cta_agregar_subc', args=[self.cuenta.slug]),
            data=self.datadict
        )

        falso_form.save.assert_called_once()

    @patch('diario.views.FormCrearSubcuenta', new_callable=patch_save)
    def test_POST_no_guarda_form_con_datos_no_validos(self, falso_FormCrearSubcuenta):
        falso_form = falso_FormCrearSubcuenta.return_value
        falso_form.is_valid.return_value = False

        self.client.post(
            reverse('cta_agregar_subc', args=[self.cuenta.slug]),
            data=self.datadict
        )

        self.assertFalse(falso_form.save.called)

    @patch('diario.views.FormCrearSubcuenta', new_callable=patch_save)
    def test_redirige_a_pag_de_cuenta_con_form_valido(self, falso_FormCrearSubcuenta):
        falso_form = falso_FormCrearSubcuenta.return_value
        falso_form.is_valid.return_value = True
        falso_form.save.return_value = self.cuenta

        response = self.client.post(
            reverse('cta_agregar_subc', args=[self.cuenta.slug]),
            data=self.datadict
        )

        self.assertRedirects(response, self.cuenta.get_absolute_url())

    def test_pasa_form_crear_subcuenta_a_template(self):
        response = self.client.get(
            reverse('cta_agregar_subc', args=[self.cuenta.slug]))

        self.assertIsInstance(response.context['form'], FormCrearSubcuenta)


class TestMovNuevo(TestCase):

    def setUp(self):
        Titular.crear(titname='tito')
        Cuenta.crear(nombre='cuenta', slug='cta')

    def test_usa_template_mov_form(self):
        response = self.client.get(reverse('mov_nuevo'))
        self.assertTemplateUsed(response, 'diario/mov_form.html')

    def test_si_no_hay_cuentas_redirige_a_crear_cuenta(self):
        Cuenta.tomar(slug='cta').delete()
        response = self.client.get(reverse('mov_nuevo'))
        self.assertRedirects(response, reverse('cta_nueva'))

    def test_no_muestra_cuentas_acumulativas_entre_las_opciones(self):
        cta_int = Cuenta.crear('cuenta interactiva', 'ci')
        cta_acum = dividir_en_dos_subcuentas(
            Cuenta.crear('cuenta_acumulativa', 'ca')
        )

        response = self.client.get(reverse('mov_nuevo'))
        opciones_ce = response.context['form'].fields['cta_entrada'].queryset
        opciones_cs = response.context['form'].fields['cta_salida'].queryset

        self.assertIn(cta_int, opciones_ce)
        self.assertNotIn(cta_acum, opciones_ce)

        self.assertIn(cta_int, opciones_cs)
        self.assertNotIn(cta_acum, opciones_cs)

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
        Titular.crear(titname='Tito')
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
        Titular.crear(titname='tito')
        self.cuenta = Cuenta.crear(nombre='Efectivo', slug='E')
        self.mov = Movimiento.crear(
            concepto='saldo', importe=166, cta_entrada=self.cuenta)

    def test_usa_template_mov_form(self):
        response = self.client.get(reverse('mov_mod', args=[self.mov.pk]))
        self.assertTemplateUsed(response, 'diario/mov_form.html')

    def test_si_mov_tiene_cuenta_acumulativa_en_campo_de_cuenta_la_muestra(self):
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)
        response = self.client.get(reverse('mov_mod', args=[self.mov.pk]))
        self.assertIn(
            self.cuenta,
            response.context['form'].fields['cta_entrada'].queryset
        )

    def test_si_cta_entrada_es_acumulativa_campo_esta_deshabilitado(self):
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)
        response = self.client.get(reverse('mov_mod', args=[self.mov.pk]))
        self.assertTrue(
            response.context['form'].fields['cta_entrada'].disabled)

    def test_si_cta_entrada_es_interactiva_campo_esta_habilitado(self):
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)
        ci = Cuenta.crear('banco', 'b')
        otro_mov = Movimiento.crear('Otro movimiento', 100, ci)
        response = self.client.get(reverse('mov_mod', args=[otro_mov.pk]))
        self.assertFalse(
            response.context['form'].fields['cta_entrada'].disabled)

    def test_si_cta_entrada_es_interactiva_no_muestra_cuentas_acumulativas_entre_las_opciones(self):
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)
        ci = Cuenta.crear('banco', 'b')
        otro_mov = Movimiento.crear('Otro movimiento', 100, ci)

        response = self.client.get(reverse('mov_mod', args=[otro_mov.pk]))

        self.assertNotIn(
            self.cuenta,
            response.context['form'].fields['cta_entrada'].queryset
        )

    def test_si_no_tiene_cta_entrada_no_muestra_cuentas_acumulativas_entre_las_opciones(self):
        otro_mov = Movimiento.crear('Otro movimiento', 100, None, self.cuenta)
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)

        response = self.client.get(reverse('mov_mod', args=[otro_mov.pk]))

        self.assertNotIn(
            self.cuenta,
            response.context['form'].fields['cta_entrada'].queryset
        )

    def test_si_cta_salida_es_acumulativa_campo_esta_deshabilitado(self):
        salida = Movimiento.crear('Salida', 100, cta_salida=self.cuenta)
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)

        response = self.client.get(reverse('mov_mod', args=[salida.pk]))
        self.assertTrue(response.context['form'].fields['cta_salida'].disabled)

    def test_si_cta_salida_es_interactiva_campo_esta_habilitado(self):
        ci = Cuenta.crear('banco', 'b')
        otro_mov = Movimiento.crear('Otro movimiento', 100, self.cuenta, ci)
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)
        response = self.client.get(reverse('mov_mod', args=[otro_mov.pk]))
        self.assertFalse(
            response.context['form'].fields['cta_salida'].disabled)

    def test_si_cta_salida_es_interactiva_no_muestra_cuentas_acumulativas_entre_las_opciones(self):
        ci = Cuenta.crear('banco', 'b')
        otro_mov = Movimiento.crear('Otro movimiento', 100, self.cuenta, ci)
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)
        response = self.client.get(reverse('mov_mod', args=[otro_mov.pk]))
        self.assertNotIn(
            self.cuenta,
            response.context['form'].fields['cta_salida'].queryset
        )

    def test_si_no_tiene_cta_salida_no_muestra_cuentas_acumulativas_entre_las_opciones(self):
        self.cuenta = dividir_en_dos_subcuentas(self.cuenta)
        response = self.client.get(reverse('mov_mod', args=[self.mov.pk]))
        self.assertNotIn(
            self.cuenta,
            response.context['form'].fields['cta_salida'].queryset
        )

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


@patch('diario.views.verificar_saldos')
class TestVerificarSaldo(TestCase):

    def setUp(self):
        super().setUp()
        Titular.crear(titname='tito')
        Cuenta.crear(nombre='cuenta', slug='cta')

    def test_verifica_saldo_de_cuentas(self, mock_verificar_saldos):
        self.client.get(reverse('verificar_saldos'))
        mock_verificar_saldos.assert_called_once()

    def test_redirige_a_home_si_no_hay_saldos_erroneos(self, mock_verificar_saldos):
        mock_verificar_saldos.return_value = []
        response = self.client.get(reverse('verificar_saldos'))
        self.assertRedirects(response, reverse('home'))

    def test_redirige_a_corregir_saldo_si_hay_saldos_erroneos(self, mock_verificar_saldos):
        cta_1 = Cuenta.crear('cta1efectivo', 'c1e')
        cta_2 = Cuenta.crear('cta2banco', 'c2b')
        mock_verificar_saldos.return_value = [cta_1, cta_2]

        response = self.client.get(reverse('verificar_saldos'))

        self.assertRedirects(
            response,
            reverse('corregir_saldo') + '?ctas=c1e!c2b',
        )

    def test_pasa_cuentas_con_saldo_erroneo_a_corregir_saldo(self, mock_verificar_saldos):
        cta_1 = Cuenta.crear('cta1efectivo', 'c1e')
        cta_2 = Cuenta.crear('cta2banco', 'c2b')
        mock_verificar_saldos.return_value = [cta_1, cta_2]

        response = self.client.get(reverse('verificar_saldos'))

        self.assertIn(cta_1.slug, response.url)
        self.assertIn(cta_2.slug, response.url)


class TestCorregirSaldo(TestCase):

    def setUp(self):
        super().setUp()
        Titular.crear(titname='titu')
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
        Titular.crear(titname='tito')
        self.cta1 = Cuenta.crear('Efectivo', 'E')
        self.cta2 = Cuenta.crear('Banco', 'B')
        self.full_url = f"{reverse('modificar_saldo', args=[self.cta1.slug])}"\
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

    @patch('diario.views.CuentaInteractiva.corregir_saldo')
    def test_corrige_saldo_de_cuenta_interactiva(self, mock_cta_corregir_saldo):
        self.client.get(self.full_url)
        mock_cta_corregir_saldo.assert_called_once()

    @patch('diario.views.CuentaAcumulativa.corregir_saldo')
    def test_corrige_saldo_de_cuenta_acumulativa(self, mock_cta_corregir_saldo):
        self.cta1.dividir_entre(['sc1', 'sc1', 0], ['sc2', 'sc2'])
        self.client.get(self.full_url)
        mock_cta_corregir_saldo.assert_called_once()


class TestAgregarMovimiento(TestCase):

    def setUp(self):
        super().setUp()
        Titular.crear(titname='titu')
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


"""
(1) Acá debería haber un comentario explicando por qué está esto.
"""