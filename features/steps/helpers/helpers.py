from math import modf as math_modf


def formatear_importe(importe):
    if type(importe) == str:
        if importe == 'cero':
            importe = 0.0
        else:
            importe = float(importe.replace(',', '.'))

    (dec, ent) = math_modf(importe)
    str_dec = str(round(dec, 2)).split('.')[1]
    str_ent = str(ent).split('.')[0]

    return f'{str_ent},{str_dec.ljust(2, "0")}'
