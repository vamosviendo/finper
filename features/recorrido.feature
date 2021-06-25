# language: es

Característica: Recorrido
    Como usuario ordinario
    quiero poder crear cuentas y movimientos
    y ver los cambios reflejados en la página

    Escenario: Crear una cuenta y verla en la homepage

        Cuando voy a la página principal
        Entonces veo que el saldo general es 0.00 pesos
        Y la grilla de cuentas está vacia
        Y la lista de movimientos está vacia

        Y veo un botón de Cuenta nueva

        Cuando cliqueo en el botón "Cuenta nueva"
        Entonces veo un formulario de cuenta

        Cuando agrego una cuenta con nombre "Efectivo"
        Entonces veo una cuenta en la grilla con nombre "efectivo"
        Y veo que el saldo de Efectivo es cero pesos
        Y veo un botón de Movimiento nuevo

        Cuando cliqueo en el botón "Movimiento nuevo"
        Entonces veo un formulario de movimiento
        Y el campo "fecha" del formulario tiene fecha de hoy como valor por defecto

        Cuando agrego un movimiento con campos
            | nombre      | valor                  |
            | concepto    | Carga de saldo inicial |
            | cta_entrada | efectivo               |
            | importe     | 50.00                  |
        Entonces veo un movimiento en la página
        Y veo que el saldo de Efectivo es 50 pesos
        Y veo que el saldo general es 50 pesos
