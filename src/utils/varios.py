from typing import Any


def el_que_no_es(referencia: Any, valor1: Any, valor2: Any) -> Any:
    if valor1 != referencia and valor2 != referencia:
        raise ValueError("Alguno de los dos valores debe ser igual al valor de referencia")
    if valor1 == valor2 == referencia:
        raise ValueError("Alguno de los dos valores debe ser distinto al valor de referencia")
    if type(valor1) != type(valor2):
        raise TypeError("Los valores a comparar deben ser del mismo tipo")
    return valor1 if referencia == valor2 else valor2