from django.test import TestCase

from finper import settings


class SettingsTest(TestCase):

    def test_huso_horario_y_lenguaje(self):
        self.assertEqual(settings.LANGUAGE_CODE, 'es-AR')
        self.assertEqual(settings.TIME_ZONE, 'America/Argentina/Buenos_Aires')

    def test_formatos_de_fecha_aceptados(self):
        self.assertFalse(settings.USE_L10N)
        self.assertIn('%d-%m-%Y', settings.DATE_INPUT_FORMATS)
