# language: es

Característica: Ver titulares
    Quiero poder ver las cuentas que pertenecen a un titular determinado
    en una página propia.
    Quiero que todas las cuentas de un titular sumen al saldo de ese titular, 
    y no al de otro.


Escenario: Ver cuentas de un titular
    Dados dos titulares
    Y tres cuentas con los siguientes valores:
        | nombre       | slug | titular | saldo |
        | cta1efectivo | c1e  | tito    |       |
        | cta2banco    | c2b  | juan    |       |
        | cta3credito  | c3c  | tito    |       |

    Cuando voy a la página principal
    Y cliqueo en el titular "Tito Gómez"
    Entonces veo un "div" de id "titulo_pag" con texto "Tito Gómez"
    Y veo que entre las cuentas de la página aparecen las cuentas 1 y 3
    Y veo que entre las cuentas de la página no aparece la cuenta 2
    Y veo que el saldo general de la página es la suma de los de las cuentas 1 y 3