from django.test import TestCase

from diario.models import Titular


class TestModelTitular(TestCase):

    def test_guarda_y_recupera_titulares(self):
        titular = Titular()
        titular.nombre = "Juan"
        titular.full_clean()
        titular.save()

        self.assertEqual(Titular.cantidad(), 1)
        tit = Titular.tomar(nombre="Juan")
