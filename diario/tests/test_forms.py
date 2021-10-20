from datetime import date
from unittest.mock import patch

from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase

from diario.forms import FormMovimiento, FormCuentaAcu, FormCuentaInt, \
    FormSubcuentas
from diario.models import Cuenta, Movimiento
from utils import errors


class TestFormCuentaInt(TestCase):

    def test_no_acepta_cuentas_sin_slug(self):
        formcta = FormCuentaInt(data={'nombre': 'Efectivo'})
        self.assertFalse(formcta.is_valid())


class TestFormCuentaAcu(TestCase):

    def test_no_acepta_cuentas_sin_slug(self):
        formcta = FormCuentaAcu(data={'nombre': 'Efectivo'})
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

    @patch('diario.forms.CuentaInteractiva.dividir_entre')
    def test_save_divide_cuenta(self, mockCuenta_dividir):
        self.form.is_valid()
        self.form.save()
        mockCuenta_dividir.assert_called_once_with(
            {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50.0},
            {'nombre': 'Cajón de arriba', 'slug': 'ecaj', 'saldo': 200.0},
        )

    def test_save_devuelve_cuenta_madre(self):
        cuenta = self.form.save()
        self.assertEqual(cuenta, Cuenta.tomar(pk=self.cta.pk))

    def test_acepta_un_campo_saldo_vacio(self):
        self.form.data.pop('form-1-saldo')
        self.assertTrue(self.form.is_valid())

    def test_no_acepta_mas_de_un_campo_saldo_vacio(self):
        self.form.data.pop('form-0-saldo')
        self.form.data.pop('form-1-saldo')
        self.assertFalse(self.form.is_valid())


class TestFormMovimiento(TestCase):

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
