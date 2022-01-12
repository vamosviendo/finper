# language: es

Característica: Dividir_cuenta
    Dada una cuenta interactiva
    quiero poder dividirla en subcuentas
    y que las subcuentas se muestren en la página de la cuenta original


Escenario: Dividir una cuenta en subcuentas
    Dada una cuenta con los siguientes valores:
        | nombre   | slug | saldo |
        | Efectivo | e    | 200   |

    Cuando voy a la página principal
    Y cliqueo en el botón "Edit" de la cuenta "Efectivo"
    Y cliqueo en el botón "Dividir en subcuentas"
    Y completo el form de dividir cuenta con estos valores:
        | nombre          | slug | saldo |
        | Cajón de arriba | ecar | 150   |
        | Billetera       | ebil |       |

    Entonces veo que el saldo de la página es 200 pesos
    Y veo 2 subcuentas en la página Efectivo
    Y las subcuentas de la página de Efectivo tienen estos valores:
        | nombre          | slug | saldo |
        | Billetera       | ebil | 50    |
        | Cajón de arriba | ecar | 150   |
    Y veo 3 movimientos en la página
    Y los movimientos en la página tienen estos valores:
        | concepto                  | detalle                                                     | importe | cuentas  |
        | Traspaso de saldo         | Saldo pasado por Efectivo a nueva subcuenta Billetera       |  50,00  | +ebil -e |
        | Traspaso de saldo         | Saldo pasado por Efectivo a nueva subcuenta Cajón de arriba | 150,00  | +ecar -e |
        | Saldo inicial de efectivo |                                                             | 200,00  | +e       |


Escenario: Asignar subcuenta a un titular distinto al dividir cuenta
    Dada una cuenta con los siguientes valores:
        | nombre   | slug | saldo |
        | Efectivo | e    | 200   |
    Y un titular con los siguientes valores:
        | titname | nombre       |
        | tit2    | Otro Titular |

    Cuando voy a la página "cta_div" de la cuenta "Efectivo"

    Entonces veo un campo "form-0-titular" en el form de id "dividir_cta"

    Cuando completo el form de dividir cuenta con estos valores:
        | nombre          | slug | saldo | titular      |
        | Cajón de arriba | ecar | 150   | Otro Titular |
        | Billetera       | ebil |       |              |
    Y voy a la página "tit_detalle" del titular "Otro Titular"

    Entonces veo una cuenta en la grilla con nombre "Cajón de arriba"
    Y no veo una cuenta "Billetera" en la grilla
    Y me detengo
    Y veo que el patrimonio de "Otro Titular" es 150 pesos
