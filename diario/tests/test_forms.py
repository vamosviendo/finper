from datetime import date
from django.test import TestCase

from diario.forms import FormMovimiento


class FormMovimientoTest(TestCase):

    def test_incluye_los_campos_necesarios(self):
        form = FormMovimiento()
        self.assertIn('input type="text" name="fecha"', form.as_p())
        self.assertIn('input type="text" name="concepto"', form.as_p())
        self.assertIn('input type="text" name="detalle"', form.as_p())
        self.assertIn('input type="number" name="importe"', form.as_p())
        self.assertIn('input type="text" name="cta_entrada"', form.as_p())
        self.assertIn('input type="text" name="cta_salida"', form.as_p())

    def test_atributos_de_campos(self):
        form = FormMovimiento()
        formp = form.as_p()
        self.assertIn('id_input_fecha', formp)
        self.assertIn('id_input_concepto', formp)
        self.assertIn('id_input_importe', formp)
        self.assertIn('id_input_cta_entrada', formp)
        self.assertIn('id_input_cta_salida', formp)
        self.assertIn('placeholder="Concepto"', formp)
        self.assertIn('placeholder="Detalle"', formp)
        self.assertIn('placeholder="Cta. de entrada"', formp)
        self.assertIn('placeholder="Cta. de salida"', formp)

    def test_muestra_fecha_de_hoy_por_defecto(self):
        form = FormMovimiento()
        cadena_fecha = date.today().strftime('%d-%m-%Y')
        self.assertInHTML(
            f'<input type="text" name="fecha" value="{cadena_fecha}" required id="id_input_fecha"/>',
            form.as_p()
        )

    def test_permite_detalle_vacio(self):
        form = FormMovimiento(
            data={
                'fecha': date.today(),
                'concepto': 'Movimiento de salida',
                'importe': 258,
                'cta_entrada': 'Banco'
            }
        )
        self.assertTrue(form.is_valid())

    def test_permite_cta_entrada_vacia(self):
        form = FormMovimiento(
            data={
                'fecha': date.today(),
                'concepto': 'Movimiento de salida',
                'detalle': 'Detalle de salida',
                'importe': 258,
                'cta_salida': 'Efectivo'
            }
        )
        self.assertTrue(form.is_valid())

    def test_permite_cta_salida_vacia(self):
        form = FormMovimiento(
            data={
                'fecha': date.today(),
                'concepto': 'Movimiento de entrada',
                'detalle': 'Detalle de entrada',
                'importe': 258,
                'cta_entrada': 'Efectivo'
            }
        )
        self.assertTrue(form.is_valid())

    def test_permite_fecha_en_formato_argentina(self):
        form = FormMovimiento(
            data ={
                'fecha': date.today().strftime('%d-%m-%Y'),
                'concepto': 'Movimiento de entrada',
                'detalle': 'Detalle de entrada',
                'importe': 258,
                'cta_entrada': 'Efectivo',
                'cta_salida': 'Banco',
            })
        self.assertTrue(form.is_valid())

    def test_no_permite_concepto_vacio(self):
        form = FormMovimiento(
            data={
                'fecha': date.today().strftime('%d-%m-%Y'),
                'importe': 5000,
                'cta_entrada': 'Banco'
            }
        )
        self.assertFalse(form.is_valid())

    def test_no_permite_importe_vacio(self):
        form = FormMovimiento(
            data={
                'fecha': date.today().strftime('%d-%m-%Y'),
                'concepto': 'Movimiento de entrada',
                'detalle': 'Detalle de entrada',
                'cta_entrada': 'Efectivo',
                'cta_salida': 'Banco',
            }
        )
        self.assertFalse(form.is_valid())

    def test_no_permite_entrada_y_salida_ambas_vacias(self):
        form = FormMovimiento(
            data={
                'fecha': date.today().strftime('%d-%m-%Y'),
                'concepto': 'Movimiento sin importe',
                'importe': 5000
            }
        )
        self.assertFalse(form.is_valid())

    def test_guarda_valor_campo_concepto_correcto_ante_form_no_valido(self):
        form = FormMovimiento(
            data={
                'fecha': date.today().strftime('%d-%m-%Y'),
                'concepto': 'Movimiento sin importe'
            }
        )
        self.assertEqual('Movimiento sin importe', form['concepto'].value())
