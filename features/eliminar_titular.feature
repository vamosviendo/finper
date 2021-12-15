#language: es
Característica: Eliminar titular
    Quiero poder eliminar titulares
    Quiero que si esos titulares tienen patrimonio, al eliminarlo se elimine
    el patrimonio, el saldo de todas sus cuentas sea llevado a cero y las 
    cuentas sean eliminadas, sean independientes o subcuentas de otra cuenta,
    interactivas o acumulativas.


Escenario: Eliminar titular sin cuentas
    Dada una cuenta
    Y dos titulares
    
    Cuando voy a la página principal
    Y cliqueo en el segundo botón de clase "link_elim_titular"
    Y cliqueo en el botón de id "id_btn_confirm"

    Entonces veo un titular en la grilla con nombre "Juan Juánez"
    Y no veo un titular "Tito Gómez" en la grilla