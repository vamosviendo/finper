from django import template

from diario.utils import saldo_general_historico
from utils.numeros import float_format

register = template.Library()


@register.simple_tag
# TODO: unificar tags en un solo módulo
def historico_general(movimiento):
    return float_format(saldo_general_historico(movimiento))


@register.simple_tag
def historico(cuenta, mov):
    return float_format(cuenta.saldo_en_mov(mov))


@register.simple_tag
def cap_historico(titular, mov):
    return float_format(titular.capital_historico(mov))
