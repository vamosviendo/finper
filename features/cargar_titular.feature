# language: es

Característica: Ver titulares
    Quiero poder ver las cuentas que pertenecen a un titular determinado
    en una página propia.
    Quiero que todas las cuentas de un titular sumen al saldo de ese titular, 
    y no al de otro.

Escenario: Cargar titular
    Cuando voy a la página principal
    Y cliqueo en el botón "Titular nuevo"
    Entonces veo un formulario de titular

    Cuando escribo "Juan" en el campo de nombre
    Y cliqueo en el botón
    Entonces soy dirigido a la página principal
    Y veo que en el menú de titulares aparece "Juan"
