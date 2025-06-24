from __future__ import annotations

from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def pageurl(context, page: int | None = None) -> str:
    request = context["request"]
    current_url = request.path

    # Al cambiar de página, si hay un movimiento seleccionado se lo deselecciona
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
