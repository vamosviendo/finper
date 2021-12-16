#language: es

Característica: Modificar titular
    Quiero poder modificar el nombre o titname de un titular


Escenario: Modificar nombre de titular
    Dado un titular con los siguientes valores:
        | titname | nombre     |
        | tito    | Tito Gómez |
    Cuando voy a la página principal
    Y cliqueo en el botón "Edit" del titular "Tito Gómez"
    Y escribo "Tito Pérez" en el campo "nombre"
    Y cliqueo en el botón
    Entonces veo un titular en la grilla con nombre "Tito Pérez"
    Y no veo un titular "Tito Gómez" en la grilla