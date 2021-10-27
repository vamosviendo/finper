# language: es

Característica: detalle_cuenta
    Quiero que la página de detalles de una cuenta
    muestre sub subcuentas si las hay
    y los movimientos relacionados con ella o con sus subcuentas


    @no_default_tit
    Escenario: Detalle de cuenta muestra saldo, titulares, subcuentas y movimientos
        Dados 3 titulares con los siguientes valores:
            | titname | nombre       |
            | juan    | Juan Pérez   |
            | tita    | Tita Gómez   |
            | cecilia | Ceci Cecilia |
        Y 2 cuentas con los siguientes valores:
            | nombre   | slug | saldo | titular |
            | Efectivo | e    | 100   | juan    |
            | Banco    | b    | 300   | tita    |
        Y la cuenta "Banco" dividida en subcuentas:
            | nombre           | slug | saldo | titular |
            | Caja de ahorro   | bca  | 100   |         |
            | Cuenta corriente | bcc  | 200   | cecilia |
        Y movimientos con estos valores:
            | concepto            | importe | cta_entrada | cta_salida |
            | Extracción bancaria | 50      | bca         | bcc        |

        Cuando voy a la página principal
        Y entro en la cuenta "Efectivo"
        Entonces veo el titular de "Efectivo"
        Y veo sólo los movimientos relacionados con "Efectivo"

        Cuando voy a la página principal
        Y entro en la cuenta "Banco"
        Entonces veo las subcuentas de "Banco"
        Y veo los titulares de las subcuentas de "Banco"
        Y veo sólo los movimientos relacionados con "Banco" o con sus subcuentas

        Cuando entro en la cuenta "Caja de ahorro"
        Entonces veo el titular de "Caja de ahorro"
        Y veo sólo los movimientos relacionados con "Caja de ahorro"

        Cuando voy a la página principal
        Y entro en la cuenta "Banco"
        Y entro en la cuenta "Cuenta corriente"
        Entonces veo el titular de "Cuenta corriente"
        Y veo sólo los movimientos relacionados con "Cuenta corriente"
