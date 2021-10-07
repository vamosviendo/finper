# language: es

Característica: Modificar cuenta

Escenario: Modificar cuenta
    Dado un titular
    Y una cuenta
    Cuando voy a la página principal
        Y cliqueo en el botón de clase "link_mod_cuenta"
        Y escribo "Nombre modificado" en el campo "nombre"
        Y cliqueo en el botón
    Entonces veo que el nombre de la cuenta es "nombre modificado"


Escenario: Modificar cuenta acumulativa
    Dado un titular
    Y una cuenta acumulativa
    Cuando voy a la página principal
        Y cliqueo en el botón de clase "link_mod_cuenta"
        Y escribo "Nombre modificado" en el campo "nombre"
        Y cliqueo en el botón
    Entonces veo que el nombre de la cuenta es "nombre modificado"
