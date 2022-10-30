# language: es

Característica: Ingresar movimiento
    Quiero poder ingresar movimientos
    y que el importe de los movimientos se refleje en los saldos
        de las cuentas involucradas
    y que entre las opciones de cuenta de entrada y de cuenta de cta_salida
        no aparezcan cuentas acumulativas.
    Quiero que si el movimiento que genero se da entre cuentas de distintos
        titulares, genere un movimiento en contrario que de cuenta de la deuda
        contraída por el titular de la cuenta receptora con el titular de la
        cuenta emisora, y quiero que el movimiento generado no pueda
        modificarse ni eliminarse.
    Quiero poder determinar que un movimiento entre cuentas de distintos
        titulares no genere deuda del receptor para con el emisor.

Escenario: Ingresar movimiento
    Dada una cuenta
    Cuando voy a la página principal
    Y cliqueo en el botón "Movimiento nuevo"
    Entonces veo un formulario de movimiento
    Y el campo "fecha" del formulario tiene fecha de hoy como valor por defecto

    Cuando agrego un movimiento con campos
        | nombre      | valor    |
        | concepto    | Entrada  |
        | cta_entrada | efectivo |
        | importe     | 50.00    |
    Entonces veo un movimiento en la página
    Y veo que el saldo de Efectivo es 50 pesos
    Y veo que el saldo general es 50 pesos

Escenario: Cuentas acumulativas no aparecen en formulario de carga de movimiento
    Dada una cuenta
    Y una cuenta acumulativa
    Cuando voy a la página principal
    Y cliqueo en el botón "Movimiento nuevo"
    Entonces veo que entre las opciones del campo "cta_entrada" figuran:
        | nombre     |
        | efectivo   |
        | efect_sub1 |
        | efect_sub2 |
    Y veo que entre las opciones del campo "cta_entrada" no figura "efectivo acumulativa"
    Y veo que entre las opciones del campo "cta_salida" figuran:
        | nombre     |
        | efectivo   |
        | efect_sub1 |
        | efect_sub2 |
    Y veo que entre las opciones del campo "cta_salida" no figura "efectivo acumulativa"


Escenario: Crear traspaso entre cuentas de distintos titulares con deuda
    Dados dos titulares
    Y dos cuentas con los siguientes valores:
        | nombre         | slug | saldo | titular |
        | cuenta de tito | ctit | 100   | tito    |
        | cuenta de juan | cjua |       | juan    |

    Cuando genero un movimiento "Préstamo" de 30 pesos de "cuenta de tito" a "cuenta de juan"

    Entonces veo entre los movimientos de la página los siguientes:
        | concepto                | detalle                     | importe | cuentas                 |
        | Préstamo                |                             | 30,00   | +cjua -ctit             |
        | Constitución de crédito | de Tito Gómez a Juan Juánez | 30,00   | +_tito-juan -_juan-tito |

    Y veo que el primer elemento dado "movimientos" incluye un "link" de clase "elim_mov"
    Y veo que el primer elemento dado "movimientos" incluye un "link" de clase "mod_mov"
    Y veo que el segundo elemento dado "movimientos" no incluye un "link" de clase "elim_mov"
    Y veo que el segundo elemento dado "movimientos" no incluye un "link" de clase "mod_mov"

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces veo una cuenta en la grilla con slug "_tito-juan" y nombre "Préstamo entre tito y juan"
    Y veo que el saldo de "Préstamo entre tito y juan" es 30 pesos

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces veo una cuenta en la grilla con slug "_juan-tito" y nombre "Préstamo entre juan y tito"
    Y veo que el saldo de "Préstamo entre juan y tito" es -30 pesos


    Cuando genero un movimiento "Préstamo" de 10 pesos de "cuenta de tito" a "cuenta de juan"

    Entonces veo entre los movimientos de la página los siguientes:
        | concepto                | detalle                     | importe | cuentas                 |
        | Préstamo                |                             | 10,00   | +cjua -ctit             |
        | Aumento de crédito      | de Tito Gómez a Juan Juánez | 10,00   | +_tito-juan -_juan-tito |

    Y veo que el segundo elemento dado "movimientos" no incluye un "link" de clase "elim_mov"
    Y veo que el segundo elemento dado "movimientos" no incluye un "link" de clase "mod_mov"

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces veo que el saldo de "Préstamo entre tito y juan" es 40 pesos

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces veo que el saldo de "Préstamo entre juan y tito" es -40 pesos


    Cuando genero un movimiento "Devolución" de 15 pesos de "cuenta de juan" a "cuenta de tito"

    Entonces veo entre los movimientos de la página los siguientes:
        | concepto                 | detalle                     | importe | cuentas                 |
        | Devolución               |                             | 15,00   | +ctit -cjua             |
        | Pago a cuenta de crédito | de Juan Juánez a Tito Gómez | 15,00   | +_juan-tito -_tito-juan |

    Y veo que el segundo elemento dado "movimientos" no incluye un "link" de clase "elim_mov"
    Y veo que el segundo elemento dado "movimientos" no incluye un "link" de clase "mod_mov"

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces veo que el saldo de "Préstamo entre tito y juan" es 25 pesos

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces veo que el saldo de "Préstamo entre juan y tito" es -25 pesos


    Cuando genero un movimiento "Devolución" de 25 pesos de "cuenta de juan" a "cuenta de tito"

    Entonces veo entre los movimientos de la página los siguientes:
        | concepto                | detalle                     | importe | cuentas                 |
        | Devolución              |                             | 25,00   | +ctit -cjua             |
        | Cancelación de crédito  | de Juan Juánez a Tito Gómez | 25,00   | +_juan-tito -_tito-juan |

    Y veo que el segundo elemento dado "movimientos" no incluye un "link" de clase "elim_mov"
    Y veo que el segundo elemento dado "movimientos" no incluye un "link" de clase "mod_mov"

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"
    Y me detengo

    Entonces no veo una cuenta con slug "_tito-juan" en la grilla

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces no veo una cuenta con slug "_juan-tito" en la grilla


Escenario: Crear traspaso entre cuentas de distintos titulares sin generar deuda
    Dados dos titulares
    Y dos cuentas con los siguientes valores:
        | nombre         | slug | saldo | titular |
        | cuenta de tito | ctit | 100   | tito    |
        | cuenta de juan | cjua |       | juan    |

    Cuando voy a la página "mov_nuevo"
    Entonces veo un campo "esgratis" en el form de id "movimiento"

    Cuando agrego un movimiento con campos
        | nombre      | valor          |
        | concepto    | Préstamo       |
        | importe     | 30             |
        | cta_entrada | cuenta de juan |
        | cta_salida  | cuenta de tito |
        | esgratis    | True           |

    Entonces veo entre los movimientos de la página los siguientes:
        | concepto | detalle | importe | cuentas     |
        | Préstamo |         | 30,00   | +cjua -ctit |

    Y no veo movimientos con concepto "Constitución de crédito"

    Cuando voy a la página "tit_detalle" del titular "Tito Gómez"

    Entonces no veo una cuenta con slug "_tito-juan" en la grilla
    Y veo que el capital de "Tito Gómez" es 70 pesos

    Cuando voy a la página "tit_detalle" del titular "Juan Juánez"

    Entonces no veo una cuenta con slug "_juan-tito" en la grilla
    Y veo que el capital de "Juan Juánez" es 30 pesos
