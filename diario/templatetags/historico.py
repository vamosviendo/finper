from django import template

from utils.numeros import float_format

register = template.Library()


@register.simple_tag
def historico(cuenta, mov):
    return float_format(cuenta.saldo_en_mov(mov))
