# language: es

Característica: Modificar cuenta

Escenario: Ir a modificar cuenta interactiva
    Dada una cuenta
    Cuando voy a la página principal
    Y cliqueo en el botón "Edit" de la cuenta "efectivo"
    Entonces soy dirigido a la página "cta_mod" de la cuenta "efectivo"


Escenario: Modificar cuenta interactiva
    Dada una cuenta

    Cuando voy a la página "cta_mod" de la cuenta "efectivo"
    Y escribo "Nombre modificado" en el campo "nombre"
    Y cliqueo en el botón
    Entonces veo que el nombre de la cuenta es "nombre modificado"


@no_default_tit
Escenario: Cambiar titular de cuenta interactiva
    Dados dos titulares
    Y una cuenta con los siguientes valores:
        | nombre   | slug | saldo | titular |
        | Efectivo | e    | 100   | juan    |

    Cuando voy a la página "cta_mod" de la cuenta "efectivo"
    Y selecciono "Tito Gómez" en el campo "titular"
    Y cliqueo en el botón
    Y voy a la página "cta_detalle" de la cuenta "efectivo"
    Entonces veo que el titular de la cuenta es "Tito Gómez"


Escenario: Modificar cuenta acumulativa
    Dada una cuenta acumulativa
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_cuenta"
    Entonces no veo el campo "titular" entre los campos del form "cuenta"

    Cuando escribo "Nombre modificado" en el campo "nombre"
    Y cliqueo en el botón
    
    Entonces veo que el nombre de la cuenta es "nombre modificado"
