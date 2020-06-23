from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Movimiento


class ModelMovimientoTest(TestCase):

    def test_guarda_movimiento_sin_detalle(self):
        Movimiento.crear(
            fecha=date.today(),
            concepto='Movimiento de salida',
            entrada=250,
            salida=250
        )
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_no_guarda_movimiento_sin_concepto(self):
        with self.assertRaises(ValidationError) as concepto_blanco:
            mov = Movimiento.crear(
                fecha=date.today(),
                detalle='Movimiento de salida',
                entrada=250,
                salida=250
            )

        self.assertIn(
            'Este campo no puede estar en blanco.',
            concepto_blanco.exception.message_dict['concepto']
        )

    def test_no_guarda_movimiento_sin_fecha(self):
        pass

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