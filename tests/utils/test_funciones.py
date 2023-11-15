from datetime import datetime
from pathlib import Path
from unittest import TestCase

from utils.archivos import fijar_mtime
from utils.numeros import float_or_none, float_format, format_float


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

    def test_devuelve_none_si_recibe_str_no_numerica(self):
        self.assertEqual(float_or_none('numero'), None)

    def test_devuelve_none_si_recibe_tipo_erroneo(self):
        self.assertEqual(float_or_none((2, 3)), None)


class TestFloatFormat(TestCase):

    def test_devuelve_float_en_forma_de_str_con_coma(self):
        self.assertEqual(float_format(2.25), "2,25")

    def test_devuelve_dos_decimales(self):
        self.assertEqual(float_format(2.2), "2,20")
        self.assertEqual(float_format(2.256), "2,26")
        self.assertEqual(float_format(2), "2,00")


class TestFormatFloat:    # Inversa de float_format()
    def test_devuelve_str_de_numeros_con_coma_como_float(self):
        assert format_float("2,25") == 2.25
        assert format_float('2.25') == 2.25
        assert format_float('2') == 2.0
