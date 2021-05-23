def float_or_none(valor):
    try:
        return float(valor)
    except TypeError:
        return None