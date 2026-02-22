def has_not_none_attr(objeto, atributo):
    return hasattr(objeto, atributo) and getattr(objeto, atributo) is not None
