# language: es

Característica: detalle_cuenta
    Quiero que la página de detalles de una cuenta
    muestre sub subcuentas si las hay
    y los movimientos relacionados con ella o con sus subcuentas

    Escenario: Mostrar saldo, subcuentas y movimientos en vista de detalle
        Dadas 2 cuentas con los siguientes valores:
            | nombre   | slug | saldo |
            | Efectivo | e    | 100   |
            | Banco    | b    | 300   |
        Y la cuenta "Banco" dividida en subcuentas:
            | nombre           | slug | saldo |
            | Caja de ahorro   | bca  | 100   |
            | Cuenta corriente | bcc  | 200   |
        Y movimientos con estos valores:
            | concepto            | importe | cta_entrada | cta_salida |
            | Extracción bancaria | 50      | bca         | bcc        |

        Cuando voy a la página principal
            Entonces veo una cuenta en la grilla con nombre "Efectivo"
            y veo una cuenta en la grilla con nombre "Banco"
            y no veo una cuenta "Caja de ahorro" en la grilla
            y no veo una cuenta "Cuenta corriente" en la grilla
            y el saldo general es la suma de los de "Efectivo" y "Banco"

        Cuando entro en la cuenta "Efectivo"
            entonces veo sólo los movimientos relacionados con "Efectivo"

        Cuando voy a la página principal
            y entro en la cuenta "Banco"
            entonces veo las subcuentas de "Banco"
            y veo sólo los movimientos relacionados con "Banco" o con sus subcuentas

        Cuando entro en la cuenta "Caja de ahorro"
            entonces veo sólo los movimientos relacionados con "Caja de ahorro"


