from django import template

register = template.Library()


@register.simple_tag
def historico(cuenta, mov):
    return cuenta.saldo_historico(mov)
