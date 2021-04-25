from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase
from django.utils.datetime_safe import date

from diario.forms import FormMovimiento
from diario.models import Cuenta
from utils import errors


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
        cuenta = Cuenta.objects.create(nombre="repetida")
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
