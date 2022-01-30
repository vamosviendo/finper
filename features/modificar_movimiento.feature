# language: es

Característica: Modificar movimiento
    Quiero poder modificar movimientos
    y que el saldo de las cuentas involucradas no cambie
        a menos que se modifiquen importes o cuentas
    y que si alguna de las cuentas involucradas es acumulativa
        no se la pueda cambiar
        y si es interactiva, no aparezcan cuentas acumulativas entre las
            opciones para cambiarla.

Escenario: Modificar movimiento
    Dada una cuenta
        Y un movimiento con los siguientes valores:
            | concepto | importe | cta_entrada | cta_salida |
            | aSaldo   | 200     | e           |            |
    Cuando voy a la página principal
        Y cliqueo en el botón de clase "class_link_mod_mov"
        Y escribo "Saldo inicial" en el campo "concepto"
        Y cliqueo en el botón
    Entonces veo que el concepto del movimiento es "Saldo inicial"
        Y veo que el saldo de la cuenta es 200 pesos


Escenario: Modificar importe o cuentas de movimiento
    Dadas 2 cuentas con los siguientes valores:
        | nombre         | slug |
        | Aefectivo      | a    |
        | Caja de ahorro | b    |
    Y 3 movimientos con los siguientes valores:
        | concepto    | importe | cta_entrada | cta_salida |
        | aSaldo      | 200     | a           |            |
        | bSaldo      | 150     |             | b          |
        | cDepósito   |  70     | b           | a          |

    Cuando voy a la página principal
        Y cliqueo en el tercer botón de clase "class_link_mod_mov"
        Y escribo "100" en el campo "importe"
        Y cliqueo en el botón
    Entonces veo que el saldo de Aefectivo es 30 pesos

    Cuando cliqueo en el segundo botón de clase "class_link_mod_mov"
        Y selecciono "aefectivo" en el campo "cta_salida"
        Y cliqueo en el botón
    Entonces veo que el saldo de Aefectivo es -120 pesos
        Y veo que el saldo de "Caja de ahorro" es 70 pesos


Escenario: Se modifica movimiento con cuenta acumulativa
    Dadas 2 cuentas con los siguientes valores:
        | nombre         | slug |
        | cta 1 efectivo | c1e  |
        | cta 2 banco    | c2b  |
    Y un movimiento con los siguientes valores:
        | concepto    | importe   | cta_entrada | cta_salida |
        | cDepósito   |  84296.57 | c2b         | c1e        |
    Y la cuenta "cta 1 efectivo" dividida en subcuentas:
        | nombre               | slug | saldo    |
        | subcuenta 1 efectivo | sc1e | 43180.67 |
        | subcuenta 2 efectivo | sc2e |          |

    Cuando voy a la página "modificar movimiento" del primer movimiento
    Entonces veo que el campo "cta_salida" está deshabilitado
    Y veo que entre las opciones del campo "cta_entrada" figuran:
        | nombre               |
        | cta 2 banco          |
        | subcuenta 1 efectivo |
        | subcuenta 2 efectivo |
    Y veo que entre las opciones del campo "cta_entrada" no figura "cta 1 efectivo"


Escenario: Se modifica gratuidad de movimiento entre cuentas de distinto titular
    Dados dos titulares
    Y 2 cuentas con los siguientes valores:
        | nombre         | slug  | titular |
        | cuenta de tito | ctito | tito    |
        | cuenta de juan | cjuan | juan    |
    Y un movimiento con los siguientes valores:
        | concepto                | importe | cta_entrada | cta_salida |
        | préstamo de juan a tito |     100 | ctito       | cjuan      |

    Cuando voy a la página "modificar movimiento" del movimiento de concepto "préstamo de juan a tito"

    Entonces veo que el checkbox "esgratis" está deseleccionado

    Cuando elijo "True" en el campo "esgratis"
    Y cliqueo en el botón

    Entonces no veo movimientos con concepto "Constitución de crédito"
    Y veo que el patrimonio de "Tito Gómez" es 100 pesos
    Y veo que el patrimonio de "Juan Juánez" es -100 pesos

    Cuando voy a la página "modificar movimiento" del movimiento de concepto "préstamo de juan a tito"
    Entonces veo que el checkbox "esgratis" está seleccionado

    Cuando elijo "False" en el campo "esgratis"
    Y cliqueo en el botón

    Entonces veo un movimiento con concepto "Constitución de crédito"
    Y veo que el patrimonio de "Tito Gómez" es 0 pesos
    Y veo que el patrimonio de "Juan Juánez" es 0 pesos

    Cuando voy a la página "modificar movimiento" del movimiento de concepto "préstamo de juan a tito"
    Entonces veo que el checkbox "esgratis" está deseleccionado
