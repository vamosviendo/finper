# language: es

Característica: Dividir_cuenta
    Dada una cuenta interactiva
    quiero poder dividirla en subcuentas
    y que las subcuentas se muestren en la página de la cuenta original


Escenario: Dividir una cuenta en subcuentas
    Dado un titular
    Y una cuenta con los siguientes valores:
        | nombre   | slug | saldo |
        | Efectivo | e    | 200   |

    Cuando voy a la página principal
    Y cliqueo en el botón "Edit"
    Y cliqueo en el botón "Dividir en subcuentas"
    Y completo el form de dividir cuenta con estos valores:
        | nombre          | slug | saldo |
        | Cajón de arriba | ecar | 150   |
        | Billetera       | ebil | 50    |

    Entonces veo que el saldo de la página es 200 pesos
    Y veo 2 subcuentas en la página Efectivo
    Y las subcuentas de la página de Efectivo tienen estos valores:
        | nombre          | slug | saldo |
        | Billetera       | ebil | 50    |
        | Cajón de arriba | ecar | 150   |
    Y veo 3 movimientos en la página
    Y los movimientos en la página tienen estos valores:
        | concepto                                                    | importe | cuentas                    |
        | Saldo inicial de efectivo                                   | 200.00  | +efectivo                  |
        | Saldo pasado por Efectivo a nueva subcuenta Cajón de arriba | 150.00  | +cajón de arriba -efectivo |
        | Saldo pasado por Efectivo a nueva subcuenta Billetera       | 50.00   | +billetera -efectivo       |
