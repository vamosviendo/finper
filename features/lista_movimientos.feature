# language: es

Característica: Lista de movimientos
    Quiero poder ver una lista de movimientos ordenados por fecha
    con los movimientos más recientes primeros


Escenario: Mostrar lista de movimientos
    Dadas dos cuentas
    Y movimientos con los siguientes valores:
        | fecha      | concepto | importe | cta_entrada | cta_salida |
        | 2021-05-23 | Compra   | 155     |             | e          |
        | 2021-06-15 | Depósito | 25.43   | b           | e          |
        | 2020-11-25 | Ingreso  | 254     | e           |            |

    Cuando voy a la página principal

    Entonces veo la siguiente lista de movimientos:
        | fecha      | concepto | importe | general | b     | e        |
        | 2021-06-15 | Depósito |   25,43 |   99,00 | 25,43 |    73,57 |
        | 2021-05-23 | Compra   |  155,00 |   99,00 |  0,00 |    99,00 |
        | 2020-11-25 | Ingreso  |  254,00 |  254,00 |  0,00 |   254,00 |
