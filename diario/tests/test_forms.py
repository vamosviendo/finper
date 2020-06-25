from datetime import date
from django.test import TestCase

from diario.forms import FormMovimiento


class FormMovimientoTest(TestCase):

    def test_incluye_los_campos_necesarios(self):
        form = FormMovimiento()
        self.assertIn('input type="text" name="fecha"', form.as_p())
        self.assertIn('input type="text" name="concepto"', form.as_p())
        self.assertIn('input type="text" name="detalle"', form.as_p())
        self.assertIn('input type="number" name="entrada"', form.as_p())
        self.assertIn('input type="number" name="salida"', form.as_p())

    def test_atributos_de_campos(self):
        form = FormMovimiento()
        formlist = form.as_pdict()
        self.assertIn('id_input_fecha', formlist['fecha'])
        self.assertIn('id_input_concepto', formlist['concepto'])
        self.assertIn('id_input_entrada', formlist['entrada'])
        self.assertIn('placeholder="Concepto"', formlist['concepto'])
        self.assertIn('placeholder="Detalle"', formlist['detalle'])

    def test_muestra_fecha_de_hoy_por_defecto(self):
        form = FormMovimiento()
        cadena_fecha = date.today().strftime('%d-%m-%Y')
        self.assertInHTML(
            f'<input type="text" name="fecha" required id="id_input_fecha" value="{cadena_fecha}"/>',
            form.as_p()
        )

    def test_permite_detalle_vacio(self):
        form = FormMovimiento(
            data={
                'fecha': date.today(),
                'concepto': 'Movimiento de salida',
                'salida': 258,
                'entrada': 258
            }
        )
        self.assertTrue(form.is_valid())

    def test_permite_entrada_vacia(self):
        form = FormMovimiento(
            data={
                'fecha': date.today(),
                'concepto': 'Movimiento de salida',
                'detalle': 'Detalle de salida',
                'salida': 258
            }
        )
        self.assertTrue(form.is_valid())

    def test_permite_salida_vacia(self):
        form = FormMovimiento(
            data={
                'fecha': date.today(),
                'concepto': 'Movimiento de entrada',
                'detalle': 'Detalle de entrada',
                'entrada': 258
            }
        )
        self.assertTrue(form.is_valid())

    def test_permite_fecha_en_formato_argentina(self):
        form = FormMovimiento(
            data ={
                'fecha': date.today().strftime('%d-%m-%Y'),
                'concepto': 'Movimiento de entrada',
                'detalle': 'Detalle de entrada',
                'entrada': 258,
                'salida': 258,
            })
        self.assertTrue(form.is_valid())

    def test_no_permite_entrada_y_salida_ambas_vacias(self):
        pass
