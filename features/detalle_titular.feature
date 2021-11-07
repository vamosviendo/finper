# language: es

Característica: Detalles titular
    Quiero poder ver las cuentas que pertenecen a un titular determinado
    en una página propia.
    Quiero que todas las cuentas de un titular sumen al saldo de ese titular, 
    y no al de otro.


@no_default_tit
Escenario: Ver detalles de un titular
    Dados dos titulares
    Y tres cuentas con los siguientes valores:
        | nombre       | slug | titular | saldo |
        | cta1efectivo | c1e  | tito    |   500 |
        | cta2banco    | c2b  | juan    |   200 |
        | cta3credito  | c3c  | tito    |   150 |

    Cuando voy a la página principal
    Y cliqueo en el titular "Tito Gómez"
    Entonces soy dirigido a la página "tit_detalle" del titular "Tito Gómez"
    Y veo un "div" de clase "nombre_titular" con texto "Tito Gómez"
    Y veo que el patrimonio de "Tito Gómez" es 650 pesos
    Y veo una cuenta en la grilla con nombre "cta1efectivo"
    Y veo una cuenta en la grilla con nombre "cta3credito"
    Y no veo una cuenta "cta2banco" en la grilla
