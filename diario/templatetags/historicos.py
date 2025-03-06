from __future__ import annotations

from django import template

from diario.models import Movimiento, Cuenta, Titular, Moneda
from diario.utils.utils_saldo import saldo_general_historico
from utils.numeros import float_format

register = template.Library()


@register.simple_tag
def historico_general(movimiento: Movimiento) -> str:
    return float_format(saldo_general_historico(movimiento))


@register.simple_tag
def historico(cuenta: Cuenta, mov: Movimiento | None) -> str:
    if mov is None:
        return float_format(cuenta.saldo)
    return float_format(cuenta.saldo_en_mov(mov))


@register.simple_tag
def cap_historico(titular: Titular, mov: Movimiento | None) -> str:
    if mov is None:
        return float_format(titular.capital)
    return float_format(titular.capital_historico(mov))


@register.simple_tag
def saldo_historico_en_moneda(cuenta: Cuenta, moneda: Moneda, mov: Movimiento | None) -> str:
    try:
        result = cuenta.saldo_en_mov_en(mov, moneda, compra=False)
    except AttributeError:  # mov is None
        result = cuenta.saldo_en(moneda, compra=False)
    return float_format(result)
