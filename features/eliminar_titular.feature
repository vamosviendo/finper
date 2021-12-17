#language: es
Característica: Eliminar titular
    Quiero poder eliminar titulares
    Quiero que si esos titulares tienen patrimonio, al eliminarlo se elimine
    el patrimonio, el saldo de todas sus cuentas sea llevado a cero y las 
    cuentas sean eliminadas, sean independientes o subcuentas de otra cuenta,
    interactivas o acumulativas.


Escenario: Eliminar titular sin cuentas
    Dados dos titulares
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_elim_titular"
    Y cliqueo en el botón de id "id_btn_confirm"

    Entonces veo un titular en la grilla con nombre "Juan Juánez"
    Y no veo un titular "Tito Gómez" en la grilla


Escenario: Eliminar titular con cuentas sin saldo
    Dados dos titulares
    Y 3 cuentas con los siguientes valores:
        | nombre   | slug | titular |
        | cuenta 1 | cta1 | tito    |
        | cuenta 2 | cta2 | tito    |
        | cuenta 3 | cta3 | juan    |
    
    Cuando voy a la página "tit_elim" del titular "Tito Gómez"
    Y cliqueo en el botón de id "id_btn_confirm"
    
    Entonces veo un titular en la grilla con nombre "Juan Juánez"
    Y veo una cuenta en la grilla con nombre "cuenta 3"
    Y no veo un titular "Tito Gómez" en la grilla
    Y no veo una cuenta "cuenta 1" en la grilla
    Y no veo una cuenta "cuenta 2" en la grilla


Escenario: Eliminar titular con cuentas con saldo
    Dados dos titulares
    Y 3 cuentas con los siguientes valores:
        | nombre   | slug | saldo | titular |
        | cuenta 1 | cta1 | -50    | tito    |
        | cuenta 2 | cta2 | 100   | tito    |
        | cuenta 3 | cta3 | 66    | juan    |
    
    Cuando voy a la página "tit_elim" del titular "Tito Gómez"
    Y cliqueo en el botón de id "id_btn_confirm"

    Entonces no veo un titular "Tito Gómez" en la grilla
    Y no veo una cuenta "cuenta 1" en la grilla
    Y no veo una cuenta "cuenta 2" en la grilla
    Y el saldo general es 66,00 pesos
    Y veo un movimiento con los siguientes valores:
        | concepto                           | importe | cta_entrada | cta_salida |
        | Retiro de patrimonio de Tito Gómez | 50      | cta1        |            |
    Y veo un movimiento con los siguientes valores:
        | concepto                           | importe | cta_entrada | cta_salida |
        | Retiro de patrimonio de Tito Gómez | 100     |             | cta2       |