from datetime import datetime
from pathlib import Path
from unittest import TestCase

from utils.funciones.archivos import fijar_mtime


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