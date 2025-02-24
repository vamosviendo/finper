from __future__ import annotations

from typing import List, Dict, Any

import pytest

from diario.models import Titular


@pytest.fixture
def dicts_subcuentas() -> List[Dict[str, Any]]:
    return [
        {'nombre': 'Subcuenta 1', 'slug': 'sc1', 'saldo': 50},
        {'nombre': 'Subcuenta 2', 'slug': 'sc2'},
    ]


@pytest.fixture
def dicts_subcuentas_sin_saldo(dicts_subcuentas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    dicts_subcuentas[0]['saldo'] = 0
    return dicts_subcuentas


@pytest.fixture
def dicts_subcuentas_otro_titular(
        dicts_subcuentas: List[Dict[str, Any]],
        otro_titular: Titular
) -> List[Dict[str, Any]]:
    dicts_subcuentas[1]["titular"] = otro_titular
    return dicts_subcuentas


@pytest.fixture
def dicts_division_gratuita(
        dicts_subcuentas_otro_titular: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    dicts_subcuentas_otro_titular[1]["esgratis"] = True
    return dicts_subcuentas_otro_titular
