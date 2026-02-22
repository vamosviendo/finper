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
        cot = Cotizacion.tomar(moneda=moneda, fecha=fecha)
    else:
        cot = moneda.cotizaciones.last()

    try:
        return float_format(getattr(cot, f"importe_{tipo}"))
    except AttributeError:  # cot is None
        return float_format(1)
