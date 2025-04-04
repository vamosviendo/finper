#language: es

Característica: Modificar titular
    Quiero poder modificar el nombre o sk de un titular


Escenario: Modificar datos de titular
    Dado un titular con los siguientes valores:
        | sk | nombre     |
        | tito    | Tito Gómez |
    Cuando voy a la página principal
    Y cliqueo en el botón "Edit" del titular "Tito Gómez"
    Y escribo "Tito Pérez" en el campo "nombre"
    Y cliqueo en el botón

    Entonces veo un titular en la grilla con nombre "Tito Pérez"
    Y no veo un titular con nombre "Tito Gómez" en la grilla

    Cuando cliqueo en el botón "Edit" del titular "Tito Pérez"
    Y escribo "titu" en el campo "sk"
    Y cliqueo en el botón

    Entonces veo un elemento de id "id_div_titular_titu"
