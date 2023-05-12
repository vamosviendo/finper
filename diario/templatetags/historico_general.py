from django import template

from diario.utils import saldo_general_historico

register = template.Library()


@register.simple_tag
# TODO: reemplazar por django.utils.formats.number_format
# TODO: unificar tags en un solo módulo
def historico_general(movimiento):
    return f'{saldo_general_historico(movimiento):.2f}'.replace('.', ',')
