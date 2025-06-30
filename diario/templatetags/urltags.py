from __future__ import annotations

from datetime import date

from django import template
from django.urls import reverse

from diario.models import Titular, Cuenta, Movimiento

register = template.Library()


@register.simple_tag
def finperurl(titular: Titular | None = None,
              cuenta: Cuenta | None = None,
              movimiento: Movimiento | None = None) -> str:
    if titular:
        if movimiento:
            return reverse("titular_movimiento", args=[titular.sk, movimiento.pk])
        return reverse("titular", args=[titular.sk])
    if cuenta:
        if movimiento:
            return reverse("cuenta_movimiento", args=[cuenta.sk, movimiento.pk])
        return reverse("cuenta", args=[cuenta.sk])
    if movimiento:
        return reverse("movimiento", args=[movimiento.pk])
    return reverse("home")


@register.simple_tag
def movurl(mov,
           tit_sk: str | None = None,
           cta_sk: str | None = None,
           page: int | None = None,
           fecha: date | None = None) -> str:
    if cta_sk:
        base_url = reverse("cuenta_movimiento", args=[cta_sk, mov.pk])
    elif tit_sk:
        base_url = reverse("titular_movimiento", args=[tit_sk, mov.pk])
    else:
        base_url = reverse("movimiento", args=[mov.pk])

    if fecha:
        return base_url + f"?fecha={fecha}"
    if page:
        return base_url + f"?page={page}"

    return base_url


@register.simple_tag(takes_context=True)
def pageurl(context, page: int | None = None) -> str:
    request = context["request"]
    current_url = request.path

    # Al cambiar de página, si hay un movimiento seleccionado se lo deselecciona
    # (se retira la letra "m" y la pk de movimiento del url)
    if "cm/" in current_url or "tm/" in current_url:
        parsed_url = current_url.split("/")
        parsed_url[2] = parsed_url[2].replace("m", "")
        parsed_url[-1] = ""
        current_url = "/".join(parsed_url)
    elif "m/" in current_url:
        current_url = "/"

    # Si no se pasa página, se permanece en la página actual
    if page:
        return f"{current_url}?page={page}#id_section_movimientos"
    else:
        return f"{current_url}#id_section_movimientos"
