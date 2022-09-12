import pytest
from django.core.exceptions import ValidationError

from diario.models import Titular


def test_no_admite_guion_en_titname():
    titular = Titular(nombre='Titular Titularini', titname='ti-ti')
    with pytest.raises(ValidationError):
        titular.full_clean()

def test_reemplaza_espacios_por_guiones_bajos():
    titular = Titular(nombre='Titular Titularini', titname='ti ti')
    titular.full_clean()
    assert titular.titname == 'ti_ti'
