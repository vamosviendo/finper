from datetime import date
from unittest.mock import patch

from django.core.exceptions import NON_FIELD_ERRORS
from django.forms import fields
from django.test import TestCase

from diario.forms import FormMovimiento, FormCuenta, \
    FormSubcuentas, FormCrearSubcuenta
from diario.models import Cuenta, CuentaInteractiva, Movimiento, Titular
from utils import errors
from utils.helpers_tests import dividir_en_dos_subcuentas


class TestFormCuenta(TestCase):

    def test_no_acepta_cuentas_sin_slug(self):
        formcta = FormCuenta(data={'nombre': 'Efectivo'})
        self.assertFalse(formcta.is_valid())

    def test_no_acepta_guion_bajo_inicial_en_slug(self):
        formcta = FormCuenta(data={'nombre': '_Efectivo', 'slug': '_efe'})
        self.assertFalse(formcta.is_valid())


class TestFormSubcuentas(TestCase):

    def setUp(self):
        super().setUp()
        self.cta = Cuenta.crear(nombre='Efectivo', slug='E')
        Movimiento.crear(
            concepto='Ingreso de saldo', importe=250, cta_entrada=self.cta)
        self.form = FormSubcuentas(
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
            cuenta=self.cta.slug,
        )
        self.subcuentas = [
            {
                'nombre': 'Billetera',
                'slug': 'ebil',
                'saldo': 50.0,
                'titular': self.cta.titular,
                'esgratis': False,
            }, {
                'nombre': 'Cajón de arriba',
                'slug': 'ecaj',
                'saldo': 200.0,
                'titular': self.cta.titular,
                'esgratis': False,
            },
        ]

    @patch('diario.forms.CuentaInteractiva.dividir_entre')
    def test_save_divide_cuenta(self, mockCuenta_dividir):
        self.form.is_valid()
        self.form.save()
        mockCuenta_dividir.assert_called_once_with(*self.subcuentas, fecha=None)

    @patch('diario.forms.FormSubcuentas.clean')
    @patch('diario.forms.CuentaInteractiva.dividir_y_actualizar')
    def test_llama_a_clean_al_salvar(self, mock_dividir_y_actualizar, mock_clean):
        def se():
            self.form.subcuentas = self.subcuentas

        mock_clean.side_effect = se
        self.form.is_valid()
        self.form.save()
        mock_clean.assert_called_once()

    @patch('diario.forms.CuentaInteractiva.dividir_y_actualizar')
    def test_save_devuelve_cuenta_madre(self, mock_dividir_y_actualizar):
        mock_dividir_y_actualizar.return_value = self.cta
        self.form.is_valid()
        cuenta = self.form.save()
        self.assertEqual(cuenta, Cuenta.tomar(pk=self.cta.pk))

    def test_acepta_un_campo_saldo_vacio(self):
        self.form.data.pop('form-1-saldo')
        self.assertTrue(self.form.is_valid())

    def test_no_acepta_mas_de_un_campo_saldo_vacio(self):
        self.form.data.pop('form-0-saldo')
        self.form.data.pop('form-1-saldo')
        self.assertFalse(self.form.is_valid())

    def test_muestra_campo_titular(self):
        self.assertIn('titular', self.form.forms[0].fields.keys())

    def test_muestra_todos_los_titulares_en_campo_titular(self):
        Titular.crear(titname='tito', nombre='Tito Gómez')
        Titular.crear(titname='juana', nombre='Juana Juani')

        self.assertEqual(
            [x[1] for x in self.form.forms[0].fields['titular'].choices],
            [tit.nombre for tit in Titular.todes()]
        )

    def test_muestra_por_defecto_titular_de_cuenta_madre(self):
        Titular.crear(titname='tito', nombre='Tito Gómez')
        Titular.crear(titname='juana', nombre='Juana Juani')

        self.assertEqual(
            self.form.forms[0].fields['titular'].initial,
            self.cta.titular
        )

    def test_no_muestra_opcion_nula_en_campo_titular(self):
        self.assertNotIn(
            '',
            [x[0] for x in self.form.forms[0].fields['titular'].choices]
        )

    @patch('diario.forms.CuentaInteractiva.dividir_y_actualizar')
    def test_pasa_titulares_correctamente_al_salvar_form(self, mock_dividir_y_actualizar):
        titular2 = Titular.crear(titname='tito', nombre='Tito Gómez')
        self.form.data.update({'form-1-titular': titular2})
        self.form.is_valid()
        self.form.save()

        self.assertEqual(
            mock_dividir_y_actualizar.call_args[0][1]['titular'],
            titular2
        )

    def test_muestra_campo_esgratis(self):
        self.assertIn('esgratis', self.form.forms[0].fields.keys())
        self.assertIsInstance(
            self.form.forms[0].fields['esgratis'],
            fields.BooleanField
        )

    def test_campo_esgratis_no_seleccionado_por_defecto(self):
        self.assertEqual(self.form.forms[0].fields['esgratis'].initial, False)

    @patch('diario.forms.Movimiento._crear_movimiento_credito')
    def test_campo_esgratis_seleccionado_en_subcuenta_con_otro_titular_no_genera_movimiento_credito(
            self, mock_crear_movimiento_credito):
        titular2 = Titular.crear(titname='tito', nombre='Tito Gómez')
        self.form.data.update({'form-1-titular': titular2})
        self.form.data.update({'form-1-esgratis': True})
        self.form.full_clean()
        self.form.save()
        mock_crear_movimiento_credito.assert_not_called()

    @patch('diario.forms.Movimiento._crear_movimiento_credito', autospec=True)
    def test_campo_esgratis_no_seleccionado_en_subcuenta_con_otro_titular_genera_movimiento_credito(
            self, mock_crear_movimiento_credito):
        titular2 = Titular.crear(titname='tito', nombre='Tito Gómez')
        self.form.data.update({'form-1-titular': titular2})
        self.form.data.update({'form-1-esgratis': False})
        self.form.full_clean()
        mov = self.form.save().subcuentas.last().movs()[0]
        mock_crear_movimiento_credito.assert_called_once_with(mov)


class TestFormCrearSubcuenta(TestCase):

    def setUp(self):
        self.cuenta = dividir_en_dos_subcuentas(Cuenta.crear('cuenta', 'cta'))
        self.formsubcuenta = FormCrearSubcuenta(data={
            'nombre': 'subcuenta nueva',
            'slug': 'sn',
        }, cuenta=self.cuenta.slug)

    @patch('diario.forms.CuentaAcumulativa.agregar_subcuenta')
    def test_llama_a_agregar_subcuenta(self, mock_agregar_subcuenta):
        self.formsubcuenta.is_valid()
        self.formsubcuenta.save()
        mock_agregar_subcuenta.assert_called_once()

    def test_cuenta_creada_es_subcuenta_de_cuenta(self):
        self.formsubcuenta.is_valid()
        self.formsubcuenta.save()
        subcuenta = CuentaInteractiva.tomar(slug='sn')
        self.assertEqual(subcuenta.cta_madre, self.cuenta)

    def test_devuelve_cuenta_madre(self):
        self.formsubcuenta.is_valid()
        cuenta = self.formsubcuenta.save()
        self.assertEqual(cuenta, self.cuenta)

    def test_muestra_campo_titular(self):
        self.assertIn('titular', self.formsubcuenta.fields.keys())

    def test_muestra_todos_los_titulares_en_campo_titular(self):
        Titular.crear(titname='tito', nombre='Tito Gómez')
        Titular.crear(titname='juana', nombre='Juana Juani')

        self.assertEqual(
            [x[1] for x in self.formsubcuenta.fields['titular'].choices],
            [tit.nombre for tit in Titular.todes()]
        )

    def test_muestra_por_defecto_titular_de_cuenta_madre(self):
        Titular.crear(titname='aalb', nombre='Aabab Aabibi')
        Titular.crear(titname='juana', nombre='Juana Juani')

        self.assertEqual(
            self.formsubcuenta.fields['titular'].initial,
            self.cuenta.titular
        )

    @patch('diario.forms.CuentaAcumulativa.agregar_subcuenta')
    def test_pasa_datos_correctamente_al_salvar_form(self, mock_agregar_subcuenta):
        titular2 = Titular.crear(titname='tito', nombre='Tito Gómez')
        self.formsubcuenta.data['titular'] = titular2
        self.formsubcuenta.is_valid()
        self.formsubcuenta.save()

        mock_agregar_subcuenta.assert_called_once_with(
            'subcuenta nueva', 'sn', titular2
        )


class TestFormMovimiento(TestCase):

    def test_acepta_movimientos_bien_formados(self):
        cuenta = Cuenta.crear(nombre='efectivo', slug='e')
        formmov = FormMovimiento(data={
            'fecha': date.today(),
            'concepto': 'movimiento bien formado',
            'importe': 150,
            'cta_entrada': cuenta,
        })
        self.assertTrue(formmov.is_valid())

    def test_no_acepta_movimientos_sin_cuentas(self):
        formmov = FormMovimiento(data={
            'fecha': date.today(),
            'concepto': 'entrada de efectivo',
            'importe': 150,
        })
        self.assertFalse(formmov.is_valid())
        self.assertIn(
            errors.CUENTA_INEXISTENTE,
            formmov.errors[NON_FIELD_ERRORS]
        )

    def test_no_acepta_cuentas_de_entrada_y_salida_iguales(self):
        cuenta = Cuenta.crear(nombre="repetida", slug='r')
        formmov = FormMovimiento(data={
            'fecha': date.today(),
            'concepto': 'entrada de efectivo',
            'importe': 150,
            'cta_entrada': cuenta,
            'cta_salida': cuenta,
        })
        self.assertFalse(formmov.is_valid())
        self.assertIn(
            errors.CUENTAS_IGUALES,
            formmov.errors[NON_FIELD_ERRORS]
        )

    def test_no_acepta_conceptos_reservados(self):
        cuenta = Cuenta.crear(nombre='efectivo', slug='e')
        for c in ['movimiento correctivo',
                  'Movimiento Correctivo',
                  'MOVIMIENTO CORRECTIVO',]:
            formmov = FormMovimiento(data={
                'fecha': date.today(),
                'concepto': c,
                'importe': 100,
                'cta_entrada': cuenta,
            })
            self.assertFalse(
                formmov.is_valid(),
                f'El concepto reservado "{c}" no debe pasar la verificación.'
            )
            self.assertIn(
                f'El concepto "{c}" está reservado para su uso '
                f'por parte del sistema',
                formmov.errors['concepto'],
            )

    def test_si_tira_error_mov_sin_cuentas_no_tira_error_cuentas_iguales(self):
        formmov = FormMovimiento(data={
            'fecha': date.today(),
            'concepto': 'entrada de efectivo',
            'importe': 150,
        })
        self.assertFalse(formmov.is_valid())
        self.assertNotIn(
            errors.CUENTAS_IGUALES,
            formmov.errors[NON_FIELD_ERRORS]
        )

    def test_toma_fecha_del_dia_por_defecto(self):
        cuenta = Cuenta.crear(nombre='efectivo', slug='e')
        formmov = FormMovimiento(data={
            'concepto': 'entrada de efectivo',
            'importe': 150,
            'cta_entrada': cuenta
        })
        self.assertEqual(formmov.fields['fecha'].initial(), date.today())

    def test_muestra_campo_esgratis(self):
        formmov = FormMovimiento()
        self.assertIn('esgratis', formmov.fields.keys())
        self.assertIsInstance(formmov.fields['esgratis'], fields.BooleanField)

    def test_campo_esgratis_no_seleccionado_por_defecto(self):
        formmov = FormMovimiento()
        self.assertEqual(formmov.fields['esgratis'].initial, False)

    def test_campo_esgratis_aparece_seleccionado_si_instancia_no_tiene_contramovimiento(self):
        cta1 = Cuenta.crear('Cuenta 1', slug='cta1')
        tit = Titular.crear(nombre='Titular 2', titname='tit2')
        cta2 = Cuenta.crear(nombre='Cuenta titular 2', slug='ctit2', titular=tit)
        mov = Movimiento.crear('Traspaso', 100, cta2, cta1, esgratis=True)
        formmov = FormMovimiento(instance=mov)
        self.assertEqual(formmov.fields['esgratis'].initial, True)

    def test_campo_esgratis_aparece_deseleccionado_si_instancia_tiene_contramovimiento(self):
        cta1 = Cuenta.crear('Cuenta 1', slug='cta1')
        tit = Titular.crear(nombre='Titular 2', titname='tit2')
        cta2 = Cuenta.crear(nombre='Cuenta titular 2', slug='ctit2', titular=tit)
        mov = Movimiento.crear('Traspaso', 100, cta2, cta1)
        formmov = FormMovimiento(instance=mov)
        self.assertEqual(formmov.fields['esgratis'].initial, False)

    @patch('diario.forms.Movimiento._crear_movimiento_credito')
    def test_campo_esgratis_seleccionado_en_movimiento_entre_titulares_no_genera_movimiento_credito(
            self, mock_crear_movimiento_credito):
        titular1 = Titular.crear(nombre='Titular 1', titname='tit1')
        titular2 = Titular.crear(nombre='Titular 2', titname='tit2')
        cuenta1 = Cuenta.crear(nombre='Cuenta titular 1', slug='ct1', titular=titular1)
        cuenta2 = Cuenta.crear(nombre='Cuenta titular 2', slug='ct2', titular=titular2)
        formmov = FormMovimiento(data={
            'fecha': date.today(),
            'concepto': 'Pago',
            'importe': 150,
            'cta_entrada': cuenta1,
            'cta_salida': cuenta2,
            'esgratis': True
        })
        formmov.full_clean()
        formmov.save()
        mock_crear_movimiento_credito.assert_not_called()
