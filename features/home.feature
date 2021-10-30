# language: es

Característica: Vista de la página principal
    Como consultante del sitio
    Quiero acceder a información general lo más completa posible en la página 
        principal


@sec
Escenario: Vistazo a la página principal
    Dado un titular con los siguientes valores:
    Y tres cuentas con los siguientes valores:
    Y tres movimientos con los siguients valores:

    Cuando voy a la página principal

    Entonces veo dos titulares en la grilla de titulares
    Y veo que el nombre del primer titular es "titular por defecto"
    Y veo que el nombre del segundo titular es "cuenta administrada"
    Y veo que el saldo del primer titular es x pesos
    Y veo que el saldo del segundo titular es x pesos
    Y veo cuentas en la grilla con los nombres "EFEC, BCO, CAJA"
    Y veo que el saldo de "efectivo" es "tantos pesos"
    Y veo que el titular de "efectivo" es "titular por defecto"
    
