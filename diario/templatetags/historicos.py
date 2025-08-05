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


@register.simple_tag
def saldo(
        dia: Dia | None = None,
        movimiento: Movimiento | None = None,
        cuenta: Cuenta | None = None,
        titular: Titular | None = None,
        moneda: Moneda | None = None,
) -> float:
    dia = dia or Dia.ultime()
    cotizacion = moneda.cotizacion_al(dia.fecha, compra=False) if moneda else 1

    if cuenta:
        if movimiento:
            result = cuenta.saldo(movimiento=movimiento)
        else:
            result = cuenta.saldo(dia=dia)
    elif titular:
        if movimiento:
            result = titular.capital(movimiento=movimiento)
        else:
            result = titular.capital(dia=dia)
    elif movimiento:
        result = saldo_general_historico(movimiento)
    else:
        result = dia.saldo()

    return round(result / cotizacion, 2)
