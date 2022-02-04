# language: es

Característica: Detalles titular
    Quiero poder ver las cuentas que pertenecen a un titular determinado
    en una página propia.
    Quiero que todas las cuentas de un titular sumen al saldo de ese titular,
    y no al de otro.
    Quiero que en la página de detalles del titular se muestren solamente los
    movimientos que involucren a las cuentas de ese titular.
    Quiero que entre los movimientos que se muestran estén también los que
    involucren a las cuentas acumulativas cuando éstas formaban parte del
    patrimonio del titular.


Escenario: Ver detalles de un titular
    Dados dos titulares
    Y tres cuentas con los siguientes valores:
        | nombre       | slug | titular | saldo |
        | cta1efectivo | c1e  | tito    |   500 |
        | cta2banco    | c2b  | juan    |   200 |
        | cta3credito  | c3c  | tito    |   150 |
    Y movimientos con estos valores:
        | concepto             | importe | cta_entrada | cta_salida |
        | 1Entrada de efectivo | 50      | c1e         |            |
        | 2Depósito en banco   | 25      | c2b         | c1e        |
        | 3Transferencia       | 20      |             | c2b        |

    Cuando voy a la página principal
    Y cliqueo en el titular "Tito Gómez"
    Entonces soy dirigido a la página "tit_detalle" del titular "Tito Gómez"
    Y veo un "div" de clase "nombre_titular" con texto "Tito Gómez"
    Y veo que el patrimonio de "Tito Gómez" es 700 pesos
    Y veo una cuenta en la grilla con nombre "cta1efectivo"
    Y veo una cuenta en la grilla con nombre "cta3credito"
    Y no veo una cuenta con nombre "cta2banco" en la grilla
    Y veo la siguiente lista de movimientos:
        | concepto                      | importe | cuentas                 |
        | 2Depósito en banco            |   25,00 | +c2b -c1e               |
        | Constitución de crédito       |   25,00 | +_tito-juan -_juan-tito |
        | 1Entrada de efectivo          |   50,00 | +c1e                    |
        | Saldo inicial de cta3credito  |  150,00 | +c3c                    |
        | Saldo inicial de cta1efectivo |  500,00 | +c1e                    |


Escenario: Se muestran movimientos de cuentas acumulativas en página de titular
    Dados dos titulares
    Y dos cuentas con los siguientes valores:
        | nombre       | slug | titular | saldo |
        | cta1efectivo | c1e  | tito    |   500 |
        | cta2banco    | c2b  | juan    |   200 |
    Y la cuenta "cta1efectivo" dividida en subcuentas:
        | nombre   | slug | titular | saldo |
        | sc1efect | sc1e | tito    | 230   |
        | sc2efect | sc2e | juan    |       |
    Y movimientos con estos valores:
        | concepto             | importe | cta_entrada | cta_salida |
        | 1Entrada de efectivo | 50      | sc1e        |            |
        | 2Entrada de efectivo | 70      | sc2e        |            |
        | 3Depósito en banco   | 25      | c2b         | sc1e       |
        | 4Transferencia       | 20      |             | c2b        |

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces veo la siguiente lista de movimientos:
        | concepto                      | importe | cuentas                 |
        | 3Depósito en banco            |   25,00 | +c2b -sc1e              |
        | Aumento de crédito            |   25,00 | +_tito-juan -_juan-tito |
        | 1Entrada de efectivo          |   50,00 | +sc1e                   |
        | Constitución de crédito       |  270,00 | +_tito-juan -_juan-tito |
        | Traspaso de saldo             |  270,00 | +sc2e -c1e              |
        | Traspaso de saldo             |  230,00 | +sc1e -c1e              |
        | Saldo inicial de cta1efectivo |  500,00 | +c1e                    |

