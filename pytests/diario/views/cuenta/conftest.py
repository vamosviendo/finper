from unittest.mock import MagicMock

import pytest


@pytest.fixture
def patch_save() -> callable:
    def patch_save_function() -> MagicMock:
        mock = MagicMock()
        mock.return_value.save.return_value.get_absolute_url.return_value = 'stub'
        return mock

    return patch_save_function
