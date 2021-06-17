# language: es

Característica: Verificar saldos
    Quiero que la primera vez que entre en la página principal
    se comprueben saldos contra movimientos
    y poder corregir saldos erróneos.

Escenario: Verificar saldos
    Dadas 2 cuentas con los siguientes valores:
        | nombre         | slug |
        | Aefectivo      | a    |
        | Caja de ahorro | b    |
    Y un movimiento con los siguientes valores:
        | concepto      | importe | cta_entrada | cta_salida |
        | Saldo inicial | 200     | a           | b          |
    Y un error de 50 pesos en el saldo de la cuenta "Aefectivo"
    Y un error de 600 pesos en el saldo de la cuenta "Caja de ahorro"

    Cuando voy a la página principal por primera vez en el día
    Entonces veo un mensaje de saldos erróneos que incluye las cuentas:
        | nombre         |
        | Aefectivo      |
        | Caja de ahorro |
    Cuando cliqueo en el botón de clase "class_btn_corregir"
        Y cliqueo en el botón de clase "class_btn_agregar"
    Entonces veo que el saldo de "Aefectivo" es 200.00 pesos
        Y veo que el saldo de "Caja de ahorro" es 400.00 pesos
        Y veo un movimiento con los siguientes valores:
            | concepto              | importe | cta_entrada    |
            | Movimiento correctivo | 600.00  | Caja de ahorro |
    Cuando introduzco un error de 50 pesos en el saldo de la cuenta "Aefectivo"
        Y voy a la página principal sin que haya cambiado el día
    Entonces veo que el saldo de "Aefectivo" es 250.00 pesos
        
Escenario: Verificar saldo en cuenta acumulativa
    Dada una cuenta con los siguientes valores:
        | nombre       | slug | saldo |
        | Banco Nación | bn   | 500   |
    Y la cuenta "Banco Nación" dividida en subcuentas:
        | nombre                        | slug | saldo |
        | Banco Nación Caja de ahorro   | bnca | 200   |
        | Banco Nación Cuenta corriente | bncc | 300   |
    Y un error de 100 pesos en el saldo de la cuenta "Banco Nación"

    Cuando voy a la página principal por primera vez en el día
    Entonces veo un mensaje de saldo erróneo para la cuenta "Banco Nación"
        Pero no veo un elemento de clase "class_btn_agregar"
    Cuando cliqueo en el botón de clase "class_btn_corregir"
    Entonces veo que el saldo de "Banco Nación" es 500.00 pesos
