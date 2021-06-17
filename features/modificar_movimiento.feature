# language: es

Característica: Modificar movimiento
    Quiero poder modificar movimientos
    y que el saldo de las cuentas involucradas no cambie
    a menos que se modifiquen importes o cuentas

Escenario: Modificar movimiento
    Dada una cuenta
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
        Y cliqueo en el botón de clase "link_mod_mov"
        Y escribo "100" en el campo "importe"
        Y cliqueo en el botón
    Entonces veo que el saldo de Aefectivo es 30.00 pesos

    Cuando cliqueo en el segundo botón de clase "link_mod_mov"
        Y selecciono "Aefectivo" en el campo "cta_salida"
        Y cliqueo en el botón
    Entonces veo que el saldo de Aefectivo es -120.00 pesos
        Y veo que el saldo de "Caja de ahorro" es 70.00 pesos
