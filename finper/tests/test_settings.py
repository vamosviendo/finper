""" Tests triviales, más que nada recordatorios de cosas que hay
    que revisar en settings."""
import os

from django.test import TestCase

from finper import settings


class SettingsTest(TestCase):

    def test_huso_horario_y_lenguaje(self):
        self.assertEqual(settings.LANGUAGE_CODE, 'es-AR')
        self.assertEqual(settings.TIME_ZONE, 'America/Argentina/Buenos_Aires')

    def test_formatos_de_fecha_aceptados(self):
        self.assertFalse(settings.USE_L10N)
        self.assertIn('%d-%m-%Y', settings.DATE_INPUT_FORMATS)

    def test_static_files_settings(self):
        static_root = os.path.join(settings.BASE_DIR, 'static')
        print(static_root)
        self.assertEqual(settings.STATIC_ROOT, static_root)

        # python manage.py collectstatic
        self.assertTrue(os.path.exists(static_root))
