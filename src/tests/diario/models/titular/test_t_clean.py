import pytest
from django.core.exceptions import ValidationError

from diario.models import Titular


def test_no_admite_guion_en_sk():
    titular = Titular(nombre='Titular Titularini', sk='ti-ti')
    with pytest.raises(ValidationError):
        titular.limpiar()


def test_reemplaza_espacios_por_guiones_bajos():
    titular = Titular(nombre='Titular Titularini', sk='ti ti')
    titular.limpiar()
    assert titular.sk == 'ti_ti'
