# language:es

Característica: Saldos históricos
    Quiero que en las listas de movimientos
    Aparezca el saldo de las cuentas mostradas al momento del movimiento


Escenario: Mostrar saldos históricos de cuentas en movimientos
    Dadas dos cuentas
    Y movimientos con los siguientes valores:
        | fecha      | concepto | importe | cta_entrada | cta_salida |
        | 2020-11-25 | Ingreso  | 254     | e           |            |
        | 2021-05-23 | Compra   | 155     |             | e          |
        | 2021-05-24 | Depósito | 20      | b           | e          |
        | 2021-06-15 | Depósito | 5.43    | b           | e          |

    Cuando voy a la página principal
    Entonces veo movimientos con los siguientes valores:
        | fecha      | concepto | importe | e      | b     |
        | 2021-06-15 | Depósito | 5,43    |  73,57 | 25,43 |
        | 2021-05-24 | Depósito | 20,00   |  79,00 | 20,00 |
        | 2021-05-23 | Compra   | 155,00  |  99,00 | 0,00  |
        | 2020-11-25 | Ingreso  | 254,00  | 254,00 | 0,00  |

    Cuando genero un movimiento con los siguientes valores:
        | fecha      | concepto     | importe | cta_entrada | cta_salida |
        | 2021-01-01 | Mov anterior | 10      | e           |            |
    Y voy a la página principal
    Entonces veo movimientos con los siguientes valores:
        | fecha      | concepto     | importe | e      | b     |
        | 2021-06-15 | Depósito     |   5,43  |  83,57 | 25,43 |
        | 2021-05-24 | Depósito     |  20,00  |  89,00 | 20,00 |
        | 2021-05-23 | Compra       | 155,00  | 109,00 | 0,00  |
        | 2021-01-01 | Mov anterior |  10,00  | 264,00 | 0,00  |
        | 2020-11-25 | Ingreso      | 254,00  | 254,00 | 0,00  |

    Cuando genero un movimiento con los siguientes valores:
        | fecha      | concepto | importe | cta_entrada | cta_salida |
        | 2021-01-01 | Otro mov | 20      | e           | b          |
    Y voy a la página principal
    Entonces veo movimientos con los siguientes valores:
        | fecha      | concepto     | importe | e      | b      |
        | 2021-06-15 | Depósito     |   5,43  | 103,57 |   5,43 |
        | 2021-05-24 | Depósito     |  20,00  | 109,00 |   0,00 |
        | 2021-05-23 | Compra       | 155,00  | 129,00 | -20,00 |
        | 2021-01-01 | Otro mov     |  20,00  | 284,00 | -20,00 |
        | 2021-01-01 | Mov anterior |  10,00  | 264,00 |   0,00 |
        | 2020-11-25 | Ingreso      | 254,00  | 254,00 |   0,00 |

    Cuando elimino movimientos con los siguientes valores:
        | fecha      | concepto |
        | 2020-11-25 | Ingreso  |
    Y voy a la página principal
    Entonces veo movimientos con los siguientes valores:
        | fecha      | concepto     | importe | e       | b      |
        | 2021-06-15 | Depósito     |    5,43 | -150,43 |   5,43 |
        | 2021-05-24 | Depósito     |   20,00 | -145,00 |   0,00 |
        | 2021-05-23 | Compra       |  155,00 | -125,00 | -20,00 |
        | 2021-01-01 | Otro mov     |   20,00 |   30,00 | -20,00 |
        | 2021-01-01 | Mov anterior |   10,00 |   10,00 |   0,00 |
