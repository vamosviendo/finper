# language: es

Característica: Dividir_cuenta
    Como administrador
    Dada una cuenta acumulativa
    quiero poder agregar una subcuenta a las ya existentes


Escenario: Agregar subcuenta a cuenta
    Dado un titular
    Y una cuenta con los siguientes valores:
        | nombre   | slug | saldo |
        | Efectivo | e    | 200   |
    
    Y la cuenta "efectivo" dividida en subcuentas:
        | nombre    | slug | saldo |
        | Cajón     | ecaj | 130   |
        | Billetera | ebil |       |

    Cuando voy a la página principal
    Y cliqueo en el botón "Edit"
    Y cliqueo en el botón "Agregar subcuenta"
    Y completo el form de agregar subcuenta con estos valores:
        | nombre   | slug |
        | Bolsillo | ebol |

    Entonces veo que el saldo de la página es 200 pesos
    Y veo 3 subcuentas en la página Efectivo
    Y las subcuentas de la página de Efectivo tienen estos valores:
        | nombre    | slug | saldo |
        | Billetera | ebil |    70 |
        | Bolsillo  | ebol |     0 |
        | Cajón     | ecaj |   130 |
    Y veo 3 movimientos en la página
    Y los movimientos en la página tienen estos valores:
        | concepto                                              | importe | cuentas              |
        | Saldo inicial de efectivo                             | 200.00  | +efectivo            |
        | Saldo pasado por Efectivo a nueva subcuenta Cajón     | 130.00  | +cajón -efectivo     |
        | Saldo pasado por Efectivo a nueva subcuenta Billetera | 70.00   | +billetera -efectivo |
