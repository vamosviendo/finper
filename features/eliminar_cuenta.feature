# language: es

Característica: Eliminar cuenta
    Quiero poder eliminar cuentas
    pero que no se me permita eliminarlas si el saldo no es cero.


Escenario: Eliminar cuenta
    Dadas 2 cuentas con los siguientes valores:
        | nombre         | slug |
        | Efectivo       | e    |
        | Caja de ahorro | b    |
    Cuando voy a la página principal
        Y cliqueo en el botón de clase "link_elim_cuenta"
        Y cliqueo en el botón de id "id_btn_confirm"
    Entonces veo una cuenta en la grilla con nombre "Efectivo"
        Y no veo una cuenta con nombre "Caja de ahorro" en la grilla


Escenario: Eliminar cuenta con saldo
    Dada una cuenta con los siguientes valores:
        | nombre         | slug | saldo |
        | aEfectivo      | a    | 100   |
    Cuando voy a la página principal
        Y cliqueo en el botón de clase "link_elim_cuenta"
    Entonces veo un mensaje de error: "No se puede eliminar cuenta con saldo"
