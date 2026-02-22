from typing import Callable

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def patch_save() -> Callable:
    def patch_save_function() -> MagicMock:
        mock = MagicMock()
        mock.return_value.save.return_value.get_absolute_url.return_value = 'stub'
        return mock

    return patch_save_function


@pytest.fixture(autouse=True)
def mock_titular_principal(mocker, titular):
    return mocker.patch('diario.forms.TITULAR_PRINCIPAL', titular.sk)
