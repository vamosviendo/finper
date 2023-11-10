from typing import Any

from django.template.defaultfilters import register


@register.filter
def dict_key(dicc: dict, clave: Any) -> Any:
    return dicc.get(clave)
