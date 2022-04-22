from django import template

from diario.utils import saldo_general_historico

register = template.Library()


@register.simple_tag
def historico_general(movimiento):
    return f'{saldo_general_historico(movimiento):.2f}'.replace('.', ',')
