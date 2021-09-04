from datetime import datetime
from pathlib import Path
from unittest import TestCase

from utils.archivos import fijar_mtime
from utils.numeros import float_or_none


class TestFijarTimestamp(TestCase):

    def setUp(self):
        self.arch = Path('archivo.txt')
        self.arch.touch()

    def tearDown(self):
        self.arch.unlink()

    def test_modifica_timestamp_de_modificacion_de_archivo(self):
        fijar_mtime(self.arch, datetime(2001, 12, 20))
        self.assertEqual(
            datetime.fromtimestamp(self.arch.stat().st_mtime),
            datetime(2001, 12, 20)
        )


class TestFloatOrNone(TestCase):

    def test_devuelve_float_si_recibe_str_o_numero(self):
        self.assertEqual(float_or_none('32'), 32.0)

    def test_devuelve_none_si_recibe_none(self):
        self.assertIsNone(float_or_none(None))