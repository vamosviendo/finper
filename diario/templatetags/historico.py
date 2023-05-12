from django import template

register = template.Library()


@register.simple_tag
# TODO: reemplazar por django.utils.formats.number_format
def historico(cuenta, mov):
    return f'{cuenta.saldo_en_mov(mov):.2f}'.replace('.', ',')
