# language: es

Característica: Ingresar movimiento
    Quiero poder ingresar movimientos
    y que el importe de los movimientos se refleje en los saldos
        de las cuentas involucradas
    y que entre las opciones de cuenta de entrada y de cuenta de cta_salida
        no aparezcan cuentas acumulativas.

Escenario: Ingresar movimiento
    Dado un titular
    Y una cuenta
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
    Dado un titular
    Y una cuenta
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
