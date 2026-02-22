from __future__ import annotations

from django import template

from diario.models import Cuenta, Dia, Moneda, Movimiento, Titular
from diario.utils.utils_saldo import saldo_general_historico
from utils.numeros import float_format

register = template.Library()


@register.simple_tag
def saldo_en_moneda(cuenta: Cuenta, moneda: Moneda, mov: Movimiento | None = None) -> str:
    if mov is None:
        kwargs = {"dia": Dia.ultime()}
    elif mov == mov.dia.movimientos.last():
        kwargs = {"dia": mov.dia}
    else:
        kwargs = {"movimiento": mov}

    return float_format(cuenta.saldo(**kwargs, moneda=moneda, compra=False))


@register.simple_tag(takes_context=True)
def saldo(
        context,
        titular: Titular | None = None,
        cuenta: Cuenta | None = None,
        dia: Dia | None = None,
        moneda: Moneda | None = None
) -> str:
    dia_explicito = dia is not None
    dia = dia or context.get("dia") or Dia.ultime()
    movimiento = None if dia_explicito else context.get("movimiento")

    titular_explicito = titular is not None
    titular =  titular or context.get("titular")
    cuenta = None if titular_explicito else cuenta or context.get("cuenta")
    ente = cuenta or titular

    if movimiento:
        result = ente.saldo(movimiento=movimiento, moneda=moneda) if ente else \
            saldo_general_historico(movimiento, moneda=moneda)
    else:
        try:
            result = ente.saldo(dia=dia, moneda=moneda, compra=False) if ente else \
                saldo_general_historico(dia=dia, moneda=moneda)
        except ValueError:  # dia is None. No hay días ni movimientos
            result = 0

    return float_format(result)
