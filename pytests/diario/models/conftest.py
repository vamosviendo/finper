from __future__ import annotations

from typing import List, Dict

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.django_db)


@pytest.fixture
def dict_subcuentas() -> List[Dict[str, str | int]]:
    return [
        {'nombre': 'Billetera', 'slug': 'ebil', 'saldo': 50},
        {'nombre': 'Cajón de arriba', 'slug': 'ecaj'},
    ]
