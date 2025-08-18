from datetime import date
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fecha_inicial() -> date:
    return date(2001, 1, 2)


@pytest.fixture
def fecha_temprana() -> date:
    return date(2008, 4, 27)


@pytest.fixture
def fecha_anterior() -> date:
    return date(2010, 9, 10)


@pytest.fixture
def fecha() -> date:
    return date(2010, 11, 12)


@pytest.fixture
def fecha_posterior() -> date:
    return date(2011, 5, 1)


@pytest.fixture
def fecha_tardia() -> date:
    return date(2015, 6, 20)


@pytest.fixture
def fecha_tardia_plus() -> date:
    return date(2017, 3, 14)


@pytest.fixture
def mock_today(mocker) -> MagicMock:
    mock = mocker.patch("diario.models.moneda.date")
    mock.today.return_value = date(2024, 5, 2)
    return mock.today
