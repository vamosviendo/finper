# language: es

Característica: Modificar cuenta

Escenario: Ir a modificar cuenta interactiva
    Dado un titular
    Y una cuenta
    Cuando voy a la página principal
    Y cliqueo en el botón "Edit" de la cuenta "efectivo"
    Entonces soy dirigido a la página "cta_mod_int" de la cuenta "efectivo"


Escenario: Ir a modificar cuenta acumulativa
    Dado un titular
    Y una cuenta acumulativa
    Cuando voy a la página principal
    Y cliqueo en el botón "Edit" de la cuenta "efectivo acumulativa"
    Entonces soy dirigido a la página "cta_mod_acu" de la cuenta "efectivo acumulativa"


Escenario: Modificar cuenta interactiva
    Dado un titular
    Y una cuenta

    Cuando voy a la página "cta_mod_int" de la cuenta "efectivo"
    Y escribo "Nombre modificado" en el campo "nombre"
    Y cliqueo en el botón
    Entonces veo que el nombre de la cuenta es "nombre modificado"


Escenario: Cambiar titular de cuenta interactiva
    Dados dos titulares
    Y una cuenta con los siguientes valores:
        | nombre   | slug | saldo | titular |
        | Efectivo | e    | 100   | juan    |

    Cuando voy a la página "cta_mod_int" de la cuenta "efectivo"
    Y selecciono "Tito Gómez" en el campo "titular"
    Y cliqueo en el botón
    Y voy a la página "cta_detalle" de la cuenta "efectivo"
    Entonces veo que el titular de la cuenta es "Tito Gómez"


Escenario: Modificar cuenta acumulativa
    Dado un titular
    Y una cuenta acumulativa
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_cuenta"
    Entonces no veo el campo "titular" entre los campos del formulario

    Cuando escribo "Nombre modificado" en el campo "nombre"
    Y cliqueo en el botón
    
    Entonces veo que el nombre de la cuenta es "nombre modificado"
