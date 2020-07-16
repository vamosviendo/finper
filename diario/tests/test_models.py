from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Movimiento

from .include import crear_entrada, crear_salida


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
        with self.assertRaises(ValidationError) as concepto_en_blanco:
            mov = Movimiento(
                fecha=date.today(),
                detalle='Movimiento de salida',
                entrada=250,
                salida=250
            )
            mov.full_clean()
            mov.save()

        self.assertEqual(Movimiento.objects.count(), 0)
        self.assertIn(
            'Este campo no puede estar en blanco.',
            concepto_en_blanco.exception.message_dict['concepto']
        )

    def test_no_guarda_movimiento_sin_fecha(self):
        with self.assertRaises(ValidationError) as fecha_en_blanco:
            mov = Movimiento(
                detalle='Detalle de movimiento',
                concepto='Movimiento de salida',
                entrada=250,
                salida=250
            )
            mov.full_clean()
            mov.save()
            self.assertEqual(Movimiento.objects.count(), 0)
            self.assertIn(
                'Este campo no puede ser nulo',
                fecha_en_blanco.exception.message_dict['fecha']
            )

    def test_guarda_movimiento_con_salida_vacia(self):
        crear_entrada()
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_guarda_movimiento_con_entrada_vacia(self):
        crear_salida()
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_crear_guarda_fecha_de_hoy_por_defecto(self):
        mov = Movimiento.crear(
            detalle='Detalle de movimiento',
            concepto='Movimiento de salida',
            entrada=250,
            salida=250
        )
        self.assertEqual(mov.fecha, date.today())