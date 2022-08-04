import pytest

from diario.models import Titular


@pytest.fixture
def titular() -> Titular:
    return Titular.crear(titname='titular', nombre='Titular')


@pytest.fixture
def otro_titular() -> Titular:
    return Titular.crear(titname='otro', nombre='Otro Titular')


@pytest.fixture
def titular_gordo() -> Titular:
    return Titular.crear(titname='gordo', nombre='Titular Gordo')
