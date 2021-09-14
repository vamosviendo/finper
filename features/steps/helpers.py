# TODO: pasar funciones de fts.base a features.steps.helpers
from fts.base import esperar


def table_to_str(tabla):
    result = ''
    if tabla.headings:
        result = '|'
    for enc in tabla.headings:
        result += enc + '|'
    result += '\n'
    for fila in tabla.rows:
        if fila.cells:
            result += '|'
        for cell in fila.cells:
            result += cell + '|'
        result += '\n'
    return result


def espacios_a_camelcase(cadena):
    lista = cadena.split(' ')
    return ''.join(lista[0:1] + [x.capitalize() for x in lista[1:]])


def espacios_a_snake(cadena):
    return '_'.join(cadena.split(' '))

@esperar
def espera(funcion):
    """ Espera el tiempo por default y ejecuta función."""
    return funcion()
