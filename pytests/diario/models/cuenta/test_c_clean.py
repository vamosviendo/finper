import pytest
from django.core.exceptions import ValidationError

from diario.models import Cuenta
from utils import errors


def test_no_permite_nombres_ni_slugs_duplicados():
    Cuenta.crear(nombre='Efectivo', slug='E')
    cuenta2 = Cuenta(nombre='Efectivo', slug='EF')

    with pytest.raises(ValidationError):
        cuenta2.full_clean()

    cuenta3 = Cuenta(nombre='Otro nombre', slug='e')

    with pytest.raises(ValidationError):
        cuenta3.full_clean()


def test_no_permite_slug_vacio():
    cuenta = Cuenta(nombre='Efectivo')
    with pytest.raises(ValidationError):
        cuenta.full_clean()


def test_cuenta_no_puede_cambiar_de_titular(titular, otro_titular):
    cuenta = Cuenta.crear('cuenta propia', 'cp', titular=titular)

    cuenta.titular = otro_titular

    with pytest.raises(errors.CambioDeTitularException):
        cuenta.full_clean()
