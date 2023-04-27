from __future__ import annotations

from typing import Any

from django.utils.formats import number_format


def float_or_none(valor: Any) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError) as e:
        return None


def float_str_coma(num: str | float, lugares: int = 2) -> str:
    return number_format(round(float(num), lugares), lugares)
