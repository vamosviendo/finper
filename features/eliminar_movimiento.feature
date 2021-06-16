# language: es

Característica: Eliminar movimiento

Escenario: Eliminar movimiento
    Dadas 2 cuentas con los siguientes valores:
        | nombre         | slug |
        | Afectivo       | a    |
        | Caja de ahorro | ca   |
    Y 3 movimientos con los siguientes valores:
        | concepto            | importe | cta_entrada | cta_salida |
        | asaldo              | 100     | a           |            |
        | bsaldo              | 200     | ca          |            |
        | entrada de efectivo | 45      | a           | ca         |

    Cuando voy a la página principal
        Y cliqueo en el botón de clase "link_elim_mov"
        Y cliqueo en el botón de id "id_btn_confirm"
    
    Entonces veo 2 movimientos en la página
        Y veo que el saldo de "Afectivo" es 45.00 pesos
    
    Cuando cliqueo en el segundo botón de clase "link_elim_mov"
        Y cliqueo en el botón de id "id_btn_confirm"
    Entonces veo que el saldo de "Afectivo" es 0.00 pesos
        Y veo que el saldo de "Caja de ahorro" es 200.00 pesos

