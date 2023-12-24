from datetime import date

import pytest

from diario.models import Dia


@pytest.fixture
def dia(fecha: date) -> Dia:
    return Dia.crear(fecha=fecha)
