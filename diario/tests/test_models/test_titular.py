from django.core.exceptions import ValidationError
from django.test import TestCase

from diario.models import Titular


class TestModelTitular(TestCase):

    def test_guarda_y_recupera_titulares(self):
        titular = Titular()
        titular.titname = "juan"
        titular.nombre = 'Juan Juánez'
        titular.full_clean()
        titular.save()

        self.assertEqual(Titular.cantidad(), 1)
        tit = Titular.tomar(titname="juan")
        self.assertEqual(tit.nombre, "Juan Juánez")

    def test_no_admite_titulares_sin_titname(self):
        titular = Titular(nombre='Juan Juánez')
        with self.assertRaises(ValidationError):
            titular.full_clean()

    def test_no_admite_titulares_con_el_mismo_titname(self):
        Titular.crear(titname='juan', nombre='Juan Juánez')
        titular2 = Titular(titname='juan', nombre='Juan Juánez')

        with self.assertRaises(ValidationError):
            titular2.full_clean()

    def test_si_no_se_proporciona_nombre_toma_titname_como_nombre(self):
        titular = Titular(titname='juan')
        titular.full_clean()

        titular.save()
        tit = Titular.tomar(titname='juan')

        self.assertEqual(tit.nombre, 'juan')
