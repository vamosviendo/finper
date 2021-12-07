from datetime import date
from unittest.mock import patch

from django.core.exceptions import NON_FIELD_ERRORS
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
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50.0, 'titular': None},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200.0, 'titular': None},
        ]

    @patch('diario.forms.CuentaInteractiva.dividir_entre')
    def test_save_divide_cuenta(self, mockCuenta_dividir):
        self.form.is_valid()
        self.form.save()
        mockCuenta_dividir.assert_called_once_with(*self.subcuentas)

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


class TestFormCrearSubcuenta(TestCase):

    def setUp(self):
        self.cuenta = dividir_en_dos_subcuentas(Cuenta.crear('cuenta', 'cta'))
        self.formsubcuenta = FormCrearSubcuenta(data={
            'nombre': 'subcuenta nueva',
            'slug': 'sn'
        }, cuenta=self.cuenta.slug)
        self.formsubcuenta.is_valid()

    @patch('diario.forms.CuentaAcumulativa.agregar_subcuenta')
    def test_llama_a_agregar_subcuenta(self, falso_agregar_subcuenta):
        self.formsubcuenta.save()
        falso_agregar_subcuenta.assert_called_once_with(
            ['subcuenta nueva', 'sn']
        )

    def test_cuenta_creada_es_subcuenta_de_cuenta(self):
        self.formsubcuenta.save()
        subcuenta = CuentaInteractiva.tomar(slug='sn')
        self.assertEqual(subcuenta.cta_madre, self.cuenta)

    def test_devuelve_cuenta_madre(self):
        cuenta = self.formsubcuenta.save()
        self.assertEqual(cuenta, self.cuenta)



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
