from __future__ import annotations

from typing import List, Dict, Any

import pytest


@pytest.fixture
def dicts_subcuentas() -> List[Dict[str, Any]]:
    return [
        {'nombre': 'Subcuenta 1', 'slug': 'sc1', 'saldo': 50},
        {'nombre': 'Subcuenta 2', 'slug': 'sc2'},
    ]


@pytest.fixture
def dicts_subcuentas_sin_saldo(dicts_subcuentas: List[Dict[str, Any]]):
    dicts_subcuentas[0]['saldo'] = 0
    return dicts_subcuentas
