import pytest
from django.core.exceptions import ValidationError

from diario.models import CuentaInteractiva


def test_completa_campo_titular_vacio_con_el_primer_titular_disponible(titular, otro_titular):
    cuenta = CuentaInteractiva(nombre='Efectivo', slug='e')
    cuenta.clean()
    assert cuenta.titular == titular


def test_si_no_hay_titulares_da_error_de_validacion():
    cuenta = CuentaInteractiva(nombre='Efectivo', slug='e')
    with pytest.raises(ValidationError):
        cuenta.clean()
