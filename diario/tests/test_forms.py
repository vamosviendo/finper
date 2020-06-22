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

    def test_la_id_de_los_campos_comienza_con_id_input(self):
        form = FormMovimiento()
        formlist = form.as_plist()
        self.assertIn('id_input_fecha', formlist[0])
        self.assertIn('id_input_concepto', formlist[1])
        self.assertIn('id_input_entrada', formlist[3])

    def test_muestra_fecha_de_hoy_por_defecto(self):
        form = FormMovimiento()
        cadena_fecha = date.today().strftime('%d-%m-%Y')
        self.assertInHTML(
            f'<input type="text" name="fecha" required id="id_input_fecha" value="{cadena_fecha}"/>',
            form.as_p()
        )

