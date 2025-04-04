# language: es

Característica: Crear titulares
    Quiero poder cargar nuevos titulares de cuenta y que aparezcan en la
    página principal
    Quiero que si no hay titulares al ingresar a cualquier página se me 
    redirija a crear titular


Escenario: Ir a crear titular
    Dado un titular
    Y una cuenta

    Cuando voy a la página principal
    Y cliqueo en el botón "Titular nuevo"
    Entonces soy dirigido a la página "tit_nuevo"


Escenario: Crear titular datos completos
    Dada una cuenta

    Cuando voy a la página "tit_nuevo"
    Y escribo "Juan" en el campo "sk"
    Y escribo "Juan Juánez" en el campo "nombre"
    Y cliqueo en el botón
    Entonces soy dirigido a la página principal
    Y veo un link de texto "Juan Juánez"


Escenario: Crear titular sin nombre
    Dada una cuenta

    Cuando voy a la página "tit_nuevo"
    Y escribo "juan" en el campo "sk"
    Y cliqueo en el botón
    Entonces soy dirigido a la página principal
    Y veo un link de texto "juan"
