import pytest


@pytest.fixture
def importe():
    return 100


@pytest.fixture
def importe_bajo():
    return 2


@pytest.fixture
def importe_alto():
    return 1800


@pytest.fixture
def importe_negativo():
    return -100
