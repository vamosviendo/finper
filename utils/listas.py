def hay_mas_de_un_none_en(lista):
    """ Devuelve True si [lista] tiene más de un None entre sus elementos."""
    nones = 0
    for elemento in lista:
        if elemento is None:
            nones += 1
            if nones > 1:
                return True
