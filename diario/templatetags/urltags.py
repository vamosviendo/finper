from __future__ import annotations

from datetime import date

from django import template
from django.urls import resolve, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def finperurl(context) -> str:
    titular = context.get("titular")
    cuenta = context.get("cuenta")
    movimiento = context.get("movimiento")
    dias = context.get("dias")
    mov_presente = movimiento and movimiento.dia in dias

    if titular:
        if mov_presente:
            return titular.get_url_with_mov(movimiento)
        return titular.get_absolute_url()

    if cuenta:
        if mov_presente:
            return cuenta.get_url_with_mov(movimiento)
        return cuenta.get_absolute_url()

    if mov_presente:
        return movimiento.get_absolute_url()

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
    resolver_match = resolve(request.path)

    # Al cambiar de página, si hay un movimiento seleccionado se lo deselecciona
    if "titular" in resolver_match.url_name:
        urlname = "titular"
        args = [resolver_match.kwargs["sk"]]
    elif "cuenta" in resolver_match.url_name:
        urlname = "cuenta"
        args = [resolver_match.kwargs["sk_cta"]]
    else:
        urlname = "home"
        args = []

    # Si no se pasa página, se permanece en la página actual
    if page:
        querydict = f"?page={page}"
    else:
        querydict = ""

    return reverse(urlname, args=args) + f"{querydict}#id_section_movimientos"
