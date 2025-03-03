from __future__ import annotations

from django import template
from django.db.models import QuerySet

from diario.models import Dia, Cuenta, Titular, Movimiento

register = template.Library()


@register.filter
def movs_seleccionados(dia: Dia, ente: Cuenta | Titular | None) -> QuerySet[Movimiento]:
    try:
        return ente.movs().filter(dia=dia)
    except AttributeError:
        return dia.movimientos
