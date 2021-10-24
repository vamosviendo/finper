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
    Dado un titular
    Y una cuenta
        Y un movimiento con los siguientes valores:
            | concepto | importe | cta_entrada | cta_salida |
            | aSaldo   | 200     | e           |            |
    Cuando voy a la página principal
        Y cliqueo en el botón de clase "link_mod_mov"
        Y escribo "Saldo inicial" en el campo "concepto"
        Y cliqueo en el botón
    Entonces veo que el concepto del movimiento es "Saldo inicial"
        Y veo que el saldo de la cuenta es 200.00 pesos


Escenario: Modificar importe o cuentas de movimiento
    Dado un titular
    Y 2 cuentas con los siguientes valores:
        | nombre         | slug |
        | Aefectivo      | a    |
        | Caja de ahorro | b    |
    Y 3 movimientos con los siguientes valores:
        | concepto    | importe | cta_entrada | cta_salida |
        | aSaldo      | 200     | a           |            |
        | bSaldo      | 150     |             | b          |
        | cDepósito   |  70     | b           | a          |

    Cuando voy a la página principal
        Y cliqueo en el botón de clase "link_mod_mov"
        Y escribo "100" en el campo "importe"
        Y cliqueo en el botón
    Entonces veo que el saldo de Aefectivo es 30.00 pesos

    Cuando cliqueo en el segundo botón de clase "link_mod_mov"
        Y selecciono "aefectivo" en el campo "cta_salida"
        Y cliqueo en el botón
    Entonces veo que el saldo de Aefectivo es -120.00 pesos
        Y veo que el saldo de "Caja de ahorro" es 70.00 pesos


Escenario: Se modifica movimiento con cuenta acumulativa
    Dado un titular
    Y 2 cuentas con los siguientes valores:
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

    Cuando voy a la página "modificar movimiento" del último movimiento
    Entonces veo que el campo "cta_salida" está deshabilitado
    Y veo que entre las opciones del campo "cta_entrada" figuran:
        | nombre               |
        | cta 2 banco          |
        | subcuenta 1 efectivo |
        | subcuenta 2 efectivo |
    Y veo que entre las opciones del campo "cta_entrada" no figura "cta 1 efectivo"

    Cuando escribo "detalle de movimiento" en el campo "detalle"
    Y cliqueo en el botón
    Y me detengo
    
    Entonces soy dirigido a la página principal
    Y veo que el importe del segundo movimiento es 43180.67
    Y veo que el importe del tercer movimiento es 41115.90
    Y veo que el saldo de la cuenta "subcuenta 1 efectivo" es 43180.67
    Y veo que el saldo de la cuenta "subcuenta 2 efectivo" es 41115.90