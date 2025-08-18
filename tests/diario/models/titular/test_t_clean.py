import pytest
from django.core.exceptions import ValidationError

from diario.models import Titular


def test_no_admite_guion_en_sk():
    titular = Titular(nombre='Titular Titularini', sk='ti-ti')
    with pytest.raises(ValidationError):
        titular.full_clean()


def test_reemplaza_espacios_por_guiones_bajos():
    titular = Titular(nombre='Titular Titularini', sk='ti ti')
    titular.full_clean()
    assert titular.sk == 'ti_ti'
