from django.db.models import QuerySet
from django.http import QueryDict


def hay_mas_de_un_none_en(lista: list) -> bool:
    """ Devuelve True si [lista] tiene más de un None entre sus elementos."""
    nones = 0
    for elemento in lista:
        if elemento is None:
            nones += 1
            if nones > 1:
                return True


def remove_duplicates(lista: list) -> list:
    """ Recibe una lista y la devuelve sin elementos duplicados."""
    return list(set(lista))


def dict2querydict(datos: dict) -> QueryDict:
    qd = QueryDict('', mutable=True)
    qd.update(datos)
    return qd


def dicts_iguales(dic1: dict, dic2: dict) -> bool:
    """ Devuelve True si ambos dicts tienen iguales claves y valores.
        Compara valores de tipo QuerySet y devuelve True si son iguales
    """
    if dic1.keys() != dic2.keys():
        return False

    for key in dic1.keys():

        value1 = dic1[key]
        value2 = dic2[key]

        if isinstance(value1, QuerySet) and isinstance(value2, QuerySet):
            if list(value1) != list(value2):
                return False
        elif isinstance(value1, dict):
            if not dicts_iguales(value1, value2):
                return False
        elif isinstance(value1, list):
            for index, item in enumerate(value1):
                if isinstance(item, dict):
                    if not dicts_iguales(item, value2[index]):
                        return False
        elif value1 != value2:
            return False

    return True


def dict_en_lista(dic: dict, lista: list[dict]) -> bool:
    """ Devuelve True si un dict está entre los de una lista."""
    for dic_lista in lista:
        if dicts_iguales(dic, dic_lista):
            return True
    return False


def listas_de_dicts_iguales(lista1: list[dict], lista2: list[dict]) -> bool:
    """ Compara dos listas de dicts y devuelve True si todos los dicts son iguales
        en ambas listas
    """
    if len(lista1) != len(lista2):
        return False

    for i, d in enumerate(lista1):
        if not dicts_iguales(d, lista2[i]):
            return False
    return True
