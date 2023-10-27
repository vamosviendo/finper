import pytest

from diario.models import Titular


@pytest.fixture
def titular(fecha) -> Titular:
    return Titular.crear(titname='titular', nombre='Titular', fecha_alta=fecha)


@pytest.fixture
def otro_titular(fecha) -> Titular:
    return Titular.crear(titname='otro', nombre='Otro Titular', fecha_alta=fecha)


@pytest.fixture
def titular_gordo(fecha) -> Titular:
    return Titular.crear(titname='gordo', nombre='Titular Gordo', fecha_alta=fecha)
