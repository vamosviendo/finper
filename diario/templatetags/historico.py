from django import template

register = template.Library()


@register.simple_tag
def historico(cuenta, mov):
    return f'{cuenta.saldo_historico(mov):.2f}'.replace('.', ',')
