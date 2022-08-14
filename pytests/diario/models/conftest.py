from __future__ import annotations

from typing import List, Dict, Any

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.django_db)


@pytest.fixture
def dicts_subcuentas() -> List[Dict[str, Any]]:
    return [
        {'nombre': 'Subcuenta 1', 'slug': 'sc1', 'saldo': 50},
        {'nombre': 'Subcuenta 2', 'slug': 'sc2'},
    ]
