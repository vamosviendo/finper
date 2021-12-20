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
        | Constitución de crédito | de Tito Gómez a Juan Juánez | 30,00   | crtitojuan  | dbjuantito |

    Cuando voy a la página de detalles de "Tito Gómez"

    Entonces veo que hay una cuenta "crtitojuan" con saldo 30 en la grilla
    Y veo que el nombre de la cuenta "crtitojuan" es "Préstamo de tito a juan"

    Cuando voy a la página de detalles de "Juan Juánez"

    Entonces veo que hay una cuenta "dbjuantito" con saldo -30 en la grilla
    Y veo que el nombre de la cuenta "dbjuantito" es "Deuda de juan con tito"
    

    Cuando genero un movimiento "Préstamo" de 10 pesos de "cuenta de tito" a "cuenta de juan"
    
    Entonces veo movimientos con los siguientes valores:
        | concepto                | detalle                     | importe | cta_entrada | cta_salida |
        | Préstamo                |                             | 10      | cjua        | ctit       |
        | Constitución de crédito | de Tito Gómez a Juan Juánez | 10      | crtitojuan  | dbjuantito |

    Cuando voy a la página de detalles de "Tito Gómez"

    Entonces veo que el saldo de la cuenta "crtitojuan" es de 40 pesos

    Cuando voy a la página de detalles de "Juan Juánez"
    
    Entonces veo que el saldo de la cuenta "dbjuantito" es de -40 pesos


    Cuando genero un movimiento "Devolución" de 15 pesos de "cuenta de juan" a "cuenta de tito"

    Entonces veo movimientos con los siguientes valores:
        | concepto                | detalle                     | importe | cta_entrada | cta_salida |
        | Devolución              |                             | 15      | ctit        | cjua       |
        | Cancelación de crédito  | de Juan Juánez a Tito Gómez | 15      | crtitojuan  | dbjuantito |

    Cuando voy a la página de detalles de "Tito Gómez"

    Entonces veo que el saldo de la cuenta "crtitojuan" es de 25 pesos

    Cuando voy a la página de detalles de "Juan Juánez"
    
    Entonces veo que el saldo de la cuenta "dbjuantito" es de -25 pesos

    
    
    Cuando genero un movimiento "Devolución" de 25 pesos de "cuenta de juan" a "cuenta de tito"

    Entonces veo movimientos con los siguientes valores:
        | concepto                | detalle                     | importe | cta_entrada | cta_salida |
        | Devolución              |                             | 25      | ctit        | cjua       |
        | Cancelación de crédito  | de Juan Juánez a Tito Gómez | 25      | crtitojuan  | dbjuantito |

    Cuando voy a la página de detalles de "Tito Gómez"

    Entonces no veo una cuenta "crtitojuan" en la grillAnd 
    
    Cuando voy a la página de detalles de "Juan Juánez"

    Entonces no veo una cuenta "dbjuantito" en la grilla
