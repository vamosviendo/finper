from __future__ import annotations

from django import template

from diario.models import Cuenta, Dia, Moneda, Movimiento, Titular
from diario.utils.utils_saldo import saldo_general_historico
from utils.numeros import float_format

register = template.Library()


@register.simple_tag
def cap_historico(titular: Titular, mov: Movimiento | None) -> str:
    return float_format(titular.capital(movimiento=mov))


@register.simple_tag
def saldo_en_moneda(cuenta: Cuenta, moneda: Moneda, mov: Movimiento | None) -> str:
    return float_format(cuenta.saldo(movimiento=mov, moneda=moneda, compra=False))


@register.simple_tag(takes_context=True)
def saldo(context, moneda: Moneda | None = None) -> str:
    dia, cuenta, titular, movimiento = (context.get(x) for x in ("dia", "cuenta", "titular", "movimiento"))
    dia = dia or Dia.ultime()
    cotizacion = moneda.cotizacion_al(dia.fecha, compra=False) if moneda else 1

    if movimiento:
        result = cuenta.saldo(movimiento=movimiento) if cuenta else \
            titular.capital(movimiento=movimiento) if titular else \
            saldo_general_historico(movimiento)
    else:
        result = cuenta.saldo(dia=dia) if cuenta else \
            titular.capital(dia=dia) if titular else \
            dia.saldo()

    return float_format(result / cotizacion)
