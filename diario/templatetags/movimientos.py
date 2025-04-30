from __future__ import annotations

from django import template
from django.db.models import QuerySet

from diario.models import Dia, Cuenta, Titular, Movimiento

register = template.Library()


@register.filter
def movs_seleccionados(dia: Dia, ente: Cuenta | Titular | None) -> QuerySet[Movimiento]:
    return dia.movimientos_filtrados(ente)
