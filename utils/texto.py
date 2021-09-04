def ultima_palabra(cadena):
    return cadena.split(" ")[-1]


def retirar_comillas(cadena):
    return ''.join(cadena.split('"'))


def retirar_comillas_simples(cadena):
    return "".join(cadena.split("'"))
