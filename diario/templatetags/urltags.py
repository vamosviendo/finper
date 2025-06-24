from __future__ import annotations

from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def pageurl(context, page: int | None = None) -> str:
    request = context["request"]
    current_url = request.path

    if page:
        return f"{current_url}?page={page}#id_section_movimientos"
    else:
        return f"{current_url}#id_section_movimientos"
