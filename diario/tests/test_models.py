from datetime import date

from django.test import TestCase

from diario.models import Movimiento

class ModelMovimientoTest(TestCase):

    def test_guarda_movimiento_con_salida_vacia(self):
        mov = Movimiento(
            fecha=date.today(),
            concepto='Movimiento de entrada',
            detalle='Detalle de entrada',
            entrada=250
        )
        mov.save()
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_guarda_movimiento_con_entrada_vacia(self):
        mov = Movimiento(
            fecha=date.today(),
            concepto='Movimiento de salida',
            detalle='Detalle de salida',
            salida=250
        )
        mov.save()
        self.assertEqual(Movimiento.objects.count(), 1)