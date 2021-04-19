from django.test import TestCase

from diario.models import Cuenta


class TestModelCuenta(TestCase):

    def test_guarda_y_recupera_cuentas(self):
        primera_cuenta = Cuenta()
        primera_cuenta.nombre = 'Efectivo'
        primera_cuenta.save()

        segunda_cuenta = Cuenta()
        segunda_cuenta.nombre = 'Caja de ahorro'
        segunda_cuenta.save()

        cuentas_guardadas = Cuenta.objects.all()
        self.assertEqual(cuentas_guardadas.count(), 2)

        primera_cuenta_guardada = cuentas_guardadas[0]
        segunda_cuenta_guardada = cuentas_guardadas[1]
        self.assertEqual(primera_cuenta_guardada.nombre, 'Efectivo')
        self.assertEqual(segunda_cuenta_guardada.nombre, 'Caja de ahorro')
