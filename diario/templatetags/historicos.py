from __future__ import annotations

from django import template

from diario.models import Movimiento, Cuenta, Titular, Moneda
from utils.numeros import float_format

register = template.Library()


@register.simple_tag
def cap_historico(titular: Titular, mov: Movimiento | None) -> str:
    return float_format(titular.capital(mov))


@register.simple_tag
def saldo_en_moneda(cuenta: Cuenta, moneda: Moneda, mov: Movimiento | None) -> str:
    try:
        result = cuenta.saldo(mov, moneda, compra=False)
    except AttributeError:  # mov is None
        result = cuenta.saldo(moneda=moneda, compra=False)
    return float_format(result)
