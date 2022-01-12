#language: es
Característica: Crédito entre titulares

Escenario: Traspaso de saldo entre cuentas de distintos titulares
    Dados dos titulares
    Y dos cuentas con los siguientes valores:
        | nombre         | slug | saldo | titular |
        | cuenta de tito | ctit | 100   | tito    |
        | cuenta de juan | cjua |       | juan    |

    Cuando genero un movimiento "Préstamo" de 30 pesos de "cuenta de tito" a "cuenta de juan"

    Entonces veo movimientos con los siguientes valores:
        | concepto                | detalle                     | importe | cta_entrada | cta_salida |
        | Préstamo                |                             | 30,00   | cjua        | ctit       |
        | Constitución de crédito | de Tito Gómez a Juan Juánez | 30,00   | _tito-juan  | _juan-tito |

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces veo una cuenta en la grilla con slug "_tito-juan" y nombre "Préstamo entre tito y juan"
    Y veo que el saldo de "Préstamo entre tito y juan" es 30 pesos

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces veo una cuenta en la grilla con slug "_juan-tito" y nombre "Préstamo entre juan y tito"
    Y veo que el saldo de "Préstamo entre juan y tito" es -30 pesos


    Cuando genero un movimiento "Préstamo" de 10 pesos de "cuenta de tito" a "cuenta de juan"

    Entonces veo movimientos con los siguientes valores:
        | concepto                | detalle                     | importe | cta_entrada | cta_salida   |
        | Préstamo                |                             | 10,00   | cjua        | ctit         |
        | Aumento de crédito      | de Tito Gómez a Juan Juánez | 10,00   | _tito-juan  | _juan-tito   |

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces veo que el saldo de "Préstamo entre tito y juan" es 40 pesos

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces veo que el saldo de "Préstamo entre juan y tito" es -40 pesos


    Cuando genero un movimiento "Devolución" de 15 pesos de "cuenta de juan" a "cuenta de tito"

    Entonces veo movimientos con los siguientes valores:
        | concepto                 | detalle                     | importe | cta_entrada | cta_salida |
        | Devolución               |                             | 15,00   | ctit        | cjua       |
        | Pago a cuenta de crédito | de Juan Juánez a Tito Gómez | 15,00   | _tito-juan  | _juan-tito |

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces veo que el saldo de "Préstamo entre tito y juan" es 25 pesos

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces veo que el saldo de "Préstamo entre juan y tito" es -25 pesos


    Cuando genero un movimiento "Devolución" de 25 pesos de "cuenta de juan" a "cuenta de tito"

    Entonces veo movimientos con los siguientes valores:
        | concepto                | detalle                     | importe | cta_entrada | cta_salida |
        | Devolución              |                             | 25,00   | ctit        | cjua       |
        | Cancelación de crédito  | de Juan Juánez a Tito Gómez | 25,00   | _tito-juan  | _juan-tito |

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces no veo una cuenta "_tito-juan" en la grilla

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces no veo una cuenta "_juan-tito" en la grilla


Escenario: 'Al eliminarse un movimiento entre titulares se elimina el contramovimiento correspondiente'
    Dados dos titulares
    Y dos cuentas con los siguientes valores:
        | nombre         | slug | saldo | titular |
        | cuenta de tito | ctit | 100   | tito    |
        | cuenta de juan | cjua |       | juan    |
    Y un movimiento con los siguientes valores:
        | concepto | importe | cta_entrada | cta_salida |
        | Préstamo | 20      | cjua        | ctit       |

    Cuando voy a la página "mov_elim" del último movimiento
    Y cliqueo en el "btn" de id "confirm"

    Entonces no veo un movimiento "Constitución de crédito" en la lista
