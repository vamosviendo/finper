def float_or_none(valor):
    try:
        return float(valor)
    except TypeError:
        return None


def float_str_coma(num, lugares=2):
    return f"{float(num):.{lugares}f}".replace('.', ',')
