from datetime import date
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fecha_inicial() -> date:
    return date(2001, 1, 1)


@pytest.fixture
def fecha_temprana() -> date:
    return date(2002, 2, 2)


@pytest.fixture
def fecha_anterior() -> date:
    return date(2003, 3, 3)


@pytest.fixture
def fecha() -> date:
    return date(2004, 4, 4)


@pytest.fixture
def fecha_posterior() -> date:
    return date(2005, 5, 5)


@pytest.fixture
def fecha_tardia() -> date:
    return date(2006, 6, 6)


@pytest.fixture
def fecha_tardia_plus() -> date:
    return date(2007, 7, 7)


@pytest.fixture
def mock_today(mocker) -> MagicMock:
    mock = mocker.patch("diario.models.moneda.date")
    mock.today.return_value = date(2008, 8, 8)
    return mock.today
