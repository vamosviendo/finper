from __future__ import annotations

from django import template

from diario.models import Movimiento, Cuenta, Titular
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
