from __future__ import annotations

from django import template

from diario.models import Cuenta, Dia, Moneda, Movimiento, Titular
from diario.utils.utils_saldo import saldo_general_historico
from utils.numeros import float_format

register = template.Library()


@register.simple_tag
def saldo_en_moneda(cuenta: Cuenta, moneda: Moneda, mov: Movimiento | None) -> str:
    return float_format(cuenta.saldo(movimiento=mov, moneda=moneda, compra=False))


@register.simple_tag(takes_context=True)
def saldo(
        context,
        titular: Titular | None = None,
        cuenta: Cuenta | None = None,
        moneda: Moneda | None = None
) -> str:
    titular_como_argumento = titular is not None
    titular = titular or context.get("titular")
    cuenta = cuenta or context.get("cuenta")
    dia, movimiento = (context.get(x) for x in ("dia", "movimiento"))
    if titular_como_argumento:
        cuenta = None

    dia = dia or Dia.ultime()
    ente = cuenta or titular

    if movimiento:
        result = ente.saldo(movimiento=movimiento, moneda=moneda) if ente else \
            saldo_general_historico(movimiento, moneda=moneda)
    else:
        try:
            result = ente.saldo(dia=dia, moneda=moneda) if ente else \
                dia.saldo(moneda=moneda)
        except AttributeError:  # dia is None. No hay días ni movimientos
            result = 0

    return float_format(result)
