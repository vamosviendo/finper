from django.http import QueryDict


def hay_mas_de_un_none_en(lista):
    """ Devuelve True si [lista] tiene más de un None entre sus elementos."""
    nones = 0
    for elemento in lista:
        if elemento is None:
            nones += 1
            if nones > 1:
                return True


def remove_duplicates(lista):
    """ Recibe una lista y la devuelve sin elementos duplicados."""
    return list(set(lista))


def dict2querydict(datos):
    qd = QueryDict('', mutable=True)
    qd.update(datos)
    return qd
