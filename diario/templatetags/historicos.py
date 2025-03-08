from __future__ import annotations

from django import template

from diario.models import Movimiento, Cuenta, Titular, Moneda
from utils.numeros import float_format

register = template.Library()


@register.simple_tag
def cap_historico(titular: Titular, mov: Movimiento | None) -> str:
    try:
        result = titular.capital_historico(mov)
    except AttributeError:  # mov is None
        result = titular.capital
    return float_format(result)


@register.simple_tag
def saldo_historico_en_moneda(cuenta: Cuenta, moneda: Moneda, mov: Movimiento | None) -> str:
    try:
        result = cuenta.saldo_en_mov_en(mov, moneda, compra=False)
    except AttributeError:  # mov is None
        result = cuenta.saldo_en(moneda, compra=False)
    return float_format(result)
