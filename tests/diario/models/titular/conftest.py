import pytest

from diario.models import Titular


@pytest.fixture(autouse=True, scope='function')
def limpiar_titulares():
    for tit in Titular.todes():
        tit.delete()
