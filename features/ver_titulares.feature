# language: es

Característica: Ver titulares
    Quiero poder ver las cuentas que pertenecen a un titular determinado
    en una página propia.
    Quiero que todas las cuentas de un titular sumen al saldo de ese titular, 
    y no al de otro.


Escenario: Ver cuentas de un titular
    Dados dos titulares
    Y tres cuentas con los siguientes valores:
        | tabla |
    Y las cuentas 1 y 3 pertenecientes al titular 1
    Y la cuenta 2 perteneciente al titular 2
    Cuando voy a la página principal
    Entonces veo un menú de titulares
    Y veo que los dos titulares forman parte de esa lista

    Cuando cliqueo en el titular 1
    Entonces veo que en el título de la página está el nombre del titular
    Y veo que entre las cuentas de la página aparecen las cuentas 1 y 3
    Y veo que entre las cuentas de la página no aparece la cuenta 2
    Y veo que el saldo general de la página es la suma de los de las cuentas 1 y 3