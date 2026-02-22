def ultima_palabra(cadena: str) -> str:
    return cadena.split(" ")[-1]


def retirar_comillas(cadena: str) -> str:
    return ''.join(cadena.split('"'))


def retirar_comillas_simples(cadena: str) -> str:
    return "".join(cadena.split("'"))


def truncar(cadena: str, tamanio: int) -> str:
    if len(cadena) < tamanio:
        return cadena
    return cadena[:tamanio-1] + '…'
