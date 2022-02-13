from unittest import TestCase


from features.steps.helpers.helpers import formatear_importe


class TestFormatearImporte(TestCase):

    def test_si_recibe_palabra_cero_devuelve_numero_cero_formateado(self):
        result = formatear_importe('cero')
        self.assertEqual(result, '0,00')

    def test_si_recibe_numero_sin_decimales_lo_devuelve_con_coma_y_decimal_cero(self):
        self.assertEqual(formatear_importe('34'), '34,00')

    def test_si_recibe_numero_con_dos_decimales_lo_devuelve_con_coma(self):
        self.assertEqual(formatear_importe('34.42'), '34,42')

    def test_si_recibe_numero_con_coma_y_dos_decimales_lo_devuelve_sin_cambios(self):
        self.assertEqual(formatear_importe('34,42'), '34,42')

    def test_si_recibe_numero_con_un_decimal_lo_devuelve_con_dos_decimales(self):
        self.assertEqual(formatear_importe('43,3'), '43,30')

    def test_si_recibe_numero_con_mas_de_dos_decimales_lo_devuelve_redondeado_a_dos_decimales(self):
        self.assertEqual(formatear_importe('43,438'), '43,44')

    def test_acepta_valores_no_string(self):
        self.assertEqual(formatear_importe(34.25), '34,25')
        self.assertEqual(formatear_importe(34), '34,00')
        self.assertEqual(formatear_importe(34.3), '34,30')
        self.assertEqual(formatear_importe(34.322), '34,32')
        self.assertEqual(formatear_importe(34.328), '34,33')