from django import template

from diario.models import Moneda, Cotizacion
from utils.numeros import float_format

register = template.Library()


@register.simple_tag(takes_context=True)
def cotizacion(context, moneda: Moneda, compra: bool) -> str:
    tipo = "compra" if compra else "venta"
    movimiento = context.get("movimiento")

    if movimiento:
        fecha = movimiento.fecha
        print(moneda, fecha)
        cot = Cotizacion.tomar(moneda=moneda, fecha=fecha)
    else:
        cot = moneda.cotizaciones.last()

    return float_format(getattr(cot, f"importe_{tipo}"))
