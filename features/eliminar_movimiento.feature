# language: es

Característica: Eliminar movimiento
    Quiero poder eliminar movimientos
    y que eso se refleje en los saldos de las cuentas involucradas

Escenario: Eliminar movimiento
    Dadas 2 cuentas con los siguientes valores:
        | nombre         | slug |
        | Afectivo       | a    |
        | Caja de ahorro | ca   |
    Y 3 movimientos con los siguientes valores:
        | concepto            | importe | cta_entrada | cta_salida |
        | asaldo              | 100     | a           |            |
        | bsaldo              | 200     | ca          |            |
        | entrada de efectivo | 45      | a           | ca         |

    Cuando voy a la página principal
        Y cliqueo en el tercer botón de clase "class_link_elim_mov"
        Y cliqueo en el botón de id "id_btn_confirm"

    Entonces veo 2 movimientos en la página
        Y veo que el saldo de "Afectivo" es 45 pesos

    Cuando cliqueo en el primer botón de clase "class_link_elim_mov"
        Y cliqueo en el botón de id "id_btn_confirm"
    Entonces veo que el saldo de "Afectivo" es cero pesos
        Y veo que el saldo de "Caja de ahorro" es 200 pesos


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
