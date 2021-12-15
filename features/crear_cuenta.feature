# language: es

Característica: Crear cuentas
    Quiero poder crear nuevas cuentas y que aparezcan en la página principal


Escenario: Crear cuenta
    Dado un titular
    Cuando voy a la página "cta_nueva"
    Entonces veo un formulario de cuenta

    Cuando escribo "efectivo" en el campo "nombre"
    Y escribo "efe" en el campo "slug"
    Y selecciono "Tito Gómez" en el campo "titular"
    Y cliqueo en el botón
    Entonces soy dirigido a la página principal
    Y veo una cuenta en la grilla con slug "EFE" y nombre "efectivo"


Escenario: Ir a crear cuenta
    Dada una cuenta

    Cuando voy a la página principal
    Y cliqueo en el botón "Cuenta nueva"
    Entonces soy dirigido a la página "cta_nueva"