# language: es

@sec
Característica: Casos de creación, modificación y eliminación de movimientos


Escenario: Casos movimiento: Crear un movimiento con cuenta de entrada
    Dada una cuenta
    Cuando voy a la página principal
    Y cliqueo en el botón "Movimiento nuevo"
    Y agrego un movimiento con campos:
        | nombre      | valor    |
        | concepto    | Entrada  |
        | cta_entrada | efectivo |
        | importe     | 50.00    |
    Entonces veo un movimiento en la página
    Y veo que el saldo de Efectivo es 50 pesos
    Y veo que el saldo general es 50 pesos


Escenario: Casos movimiento: Crear un movimiento con cuenta de salida
    Dada una cuenta
    Cuando voy a la página principal
    Y cliqueo en el botón "Movimiento nuevo"
    Y agrego un movimiento con campos:
        | nombre      | valor    |
        | concepto    | Entrada  |
        | cta_salida  | efectivo |
        | importe     | 50.00    |
    Entonces veo un movimiento en la página
    Y veo que el saldo de Efectivo es -50 pesos
    Y veo que el saldo general es -50 pesos


Escenario: Casos movimiento: Crear un movimiento con cuenta de entrada y cuenta de salida
    Dadas dos cuentas
    Cuando voy a la página principal
    Y cliqueo en el botón "Movimiento nuevo"
    Y agrego un movimiento con campos:
        | nombre       | valor    |
        | concepto     | Entrada  |
        | cta_entrada  | efectivo |
        | cta_salida   | banco    |
        | importe      | 50.00    |
    Entonces veo un movimiento en la página
    Y veo que el saldo de Efectivo es 50 pesos
    Y veo que el saldo de Banco es -50 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Modificar importe en movimiento de entrada
    Dada una cuenta
    Y un movimiento con los siguientes valores:
        | concepto | importe | cta_entrada | cta_salida |
        | aSaldo   | 200     | e           |            |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el importe del movimiento "aSaldo" es 150 pesos
    Y veo que el saldo de Efectivo es 150 pesos
    Y veo que el saldo general es 150 pesos


Escenario: Casos movimiento: Modificar importe en movimiento de salida
    Dada una cuenta
    Y un movimiento con los siguientes valores:
        | concepto | importe | cta_entrada | cta_salida |
        | aSaldo   | 200     |             | e          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el importe del movimiento "aSaldo" es 150 pesos
    Y veo que el saldo de Efectivo es -150 pesos
    Y veo que el saldo general es -150 pesos


Escenario: Casos movimiento: Modificar importe en movimiento de traspaso
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el importe del movimiento "traspaso" es 150 pesos
    Y veo que el saldo de Efectivo es 150 pesos
    Y veo que el saldo de Banco es -150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Agregar cuenta de salida a movimiento de entrada
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           |            |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que la cuenta de salida del movimiento "traspaso" es "Banco"
    Y veo que el saldo de Efectivo es 200 pesos
    Y veo que el saldo de Banco es -200 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Agregar cuenta de entrada a movimiento de salida
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     |             | b          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "efectivo" en el campo "cta_entrada"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "Efectivo"
    Y veo que el saldo de Efectivo es 200 pesos
    Y veo que el saldo de Banco es -200 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Agregar cuenta de salida y modificar importe en movimiento de entrada 
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           |            |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de salida del movimiento "traspaso" es "Banco"
    Y veo que el saldo de Efectivo es 150 pesos
    Y veo que el saldo de Banco es -150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Agregar cuenta de entrada y modificar importe en movimiento de salida 
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     |             | b          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "efectivo" en el campo "cta_entrada"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "Efectivo"
    Y veo que el saldo de Efectivo es 150 pesos
    Y veo que el saldo de Banco es -150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Convertir movimiento de entrada en movimiento de salida
    Dada una cuenta
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | entrada  | 200     | e           |            |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "nada" en el campo "cta_entrada"
    Y selecciono "efectivo" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que el movimiento "entrada" no tiene cuenta de entrada
    Y veo que la cuenta de salida del movimiento "entrada" es "efectivo"
    Y veo que el saldo de efectivo es -200 pesos
    Y veo que el saldo general es -200 pesos


Escenario: Casos movimiento: Convertir movimiento de salida en movimiento de entrada
    Dada una cuenta
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | salida   | 200     |             | e          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "efectivo" en el campo "cta_entrada"
    Y selecciono "nada" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que el movimiento "salida" no tiene cuenta de salida
    Y veo que la cuenta de entrada del movimiento "salida" es "efectivo"
    Y veo que el saldo de efectivo es 200 pesos
    Y veo que el saldo general es 200 pesos


Escenario: Casos movimiento: Convertir movimiento de entrada en movimiento de salida y modificar importe
    Dada una cuenta
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | entrada  | 200     | e           |            |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "nada" en el campo "cta_entrada"
    Y selecciono "efectivo" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el movimiento "entrada" no tiene cuenta de entrada
    Y veo que la cuenta de salida del movimiento "entrada" es "efectivo"
    Y veo que el saldo de efectivo es -150 pesos
    Y veo que el saldo general es -150 pesos


Escenario: Casos movimiento: Convertir movimiento de salida en movimiento de entrada y modificar importe
    Dada una cuenta
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | salida   | 200     |             | e          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "efectivo" en el campo "cta_entrada"
    Y selecciono "nada" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el movimiento "salida" no tiene cuenta de salida
    Y veo que la cuenta de entrada del movimiento "salida" es "efectivo"
    Y veo que el saldo de efectivo es 150 pesos
    Y veo que el saldo general es 150 pesos


Escenario: Casos movimiento: Convertir movimiento de entrada en movimiento de salida y cambiar cuenta
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | entrada  | 200     | e           |            |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "nada" en el campo "cta_entrada"
    Y selecciono "banco" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que el movimiento "entrada" no tiene cuenta de entrada
    Y veo que la cuenta de salida del movimiento "entrada" es "banco"
    Y veo que el saldo de efectivo es 0 pesos
    Y veo que el saldo de banco es -200 pesos
    Y veo que el saldo general es -200 pesos


Escenario: Casos movimiento: Convertir movimiento de salida en movimiento de entrada y cambiar cuenta
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | salida   | 200     |             | e          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_entrada"
    Y selecciono "nada" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que el movimiento "salida" no tiene cuenta de salida
    Y veo que la cuenta de entrada del movimiento "salida" es "banco"
    Y veo que el saldo de efectivo es 0 pesos
    Y veo que el saldo de banco es 200 pesos
    Y veo que el saldo general es 200 pesos


Escenario: Casos movimiento: Convertir movimiento de entrada en movimiento de salida, modificar importe y cambiar cuenta
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | entrada  | 200     | e           |            |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "nada" en el campo "cta_entrada"
    Y selecciono "banco" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el movimiento "entrada" no tiene cuenta de entrada
    Y veo que la cuenta de salida del movimiento "entrada" es "banco"
    Y veo que el saldo de efectivo es 0 pesos
    Y veo que el saldo de banco es -150 pesos
    Y veo que el saldo general es -150 pesos


Escenario: Casos movimiento: Convertir movimiento de salida en movimiento de entrada, modificar importe y cambiar cuenta
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | salida   | 200     |             | e          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_entrada"
    Y selecciono "nada" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el movimiento "salida" no tiene cuenta de salida
    Y veo que la cuenta de entrada del movimiento "salida" es "banco"
    Y veo que el saldo de efectivo es 0 pesos
    Y veo que el saldo de banco es 150 pesos
    Y veo que el saldo general es 150 pesos


Escenario: Casos movimiento: Retirar cuenta de salida de movimiento de traspaso 
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "---------" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que el movimiento "traspaso" no tiene cuenta de salida
    Y veo que "banco" no está entre las cuentas del movimiento "traspaso"
    Y veo que el saldo de Efectivo es 200 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo general es 200 pesos


Escenario: Casos movimiento: Retirar cuenta de entrada de movimiento de traspaso 
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "---------" en el campo "cta_entrada"
    Y cliqueo en el botón

    Entonces veo que el movimiento "traspaso" no tiene cuenta de entrada
    Y veo que "efectivo" no está entre las cuentas del movimiento "traspaso"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es -200 pesos
    Y veo que el saldo general es -200 pesos


Escenario: Casos movimiento: Retirar cuenta de salida y modificar importe en movimiento de traspaso 
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "---------" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el movimiento "traspaso" no tiene cuenta de salida
    Y veo que "banco" no está entre las cuentas del movimiento "traspaso"
    Y veo que el saldo de Efectivo es 150 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo general es 150 pesos


Escenario: Casos movimiento: Retirar cuenta de entrada y modificar importe en movimiento de traspaso 
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "---------" en el campo "cta_entrada"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el movimiento "traspaso" no tiene cuenta de entrada
    Y veo que "efectivo" no está entre las cuentas del movimiento "traspaso"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es -150 pesos
    Y veo que el saldo general es -150 pesos


Escenario: Casos movimiento: Cambiar cuenta en movimiento de entrada
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | entrada  | 200     | e           |            |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_entrada"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "entrada" es "banco"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 200 pesos
    Y veo que el saldo general es 200 pesos


Escenario: Casos movimiento: Cambiar cuenta en movimiento de salida
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | salida   | 200     |             | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "efectivo" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que la cuenta de salida del movimiento "salida" es "efectivo"
    Y veo que el saldo de Efectivo es -200 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo general es -200 pesos


Escenario: Casos movimiento: Cambiar cuenta y modificar importe en movimiento de entrada
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | entrada  | 200     | e           |            |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_entrada"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "entrada" es "banco"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 150 pesos
    Y veo que el saldo general es 150 pesos


Escenario: Casos movimiento: Cambiar cuenta y modificar importe en movimiento de salida
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | salida   | 200     |             | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "efectivo" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de salida del movimiento "salida" es "efectivo"
    Y veo que el saldo de Efectivo es -150 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo general es -150 pesos


Escenario: Casos movimiento: Cambiar cuenta de entrada en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_entrada"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es -200 pesos
    Y veo que el saldo de Caja es 200 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Cambiar cuenta de salida en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que la cuenta de salida del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 200 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es -200 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Cambiar cuenta de entrada y modificar importe en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_entrada"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es -150 pesos
    Y veo que el saldo de Caja es 150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Cambiar cuenta de salida y modificar importe en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de salida del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 150 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es -150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Cambiar cuenta de entrada y cuenta de salida en movimiento de traspaso
    Dadas cuatro cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_entrada"
    Y selecciono "crédito" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "caja"
    Y veo que la cuenta de salida del movimiento "traspaso" es "crédito"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es 200 pesos
    Y veo que el saldo de Crédito es -200 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Cambiar cuenta de entrada y cuenta de salida y modificar importe en movimiento de traspaso
    Dadas cuatro cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_entrada"
    Y selecciono "crédito" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es 150 pesos
    Y veo que el saldo de Crédito es -150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Retirar cuenta de entrada y cambiar cuenta de salida en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "nada" en el campo "cta_entrada"
    Y selecciono "caja" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que el movimiento "traspaso" no tiene cuenta de entrada
    Y veo que "efectivo" no está entre las cuentas del movimiento "traspaso"
    Y veo que la cuenta de salida del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es -200 pesos
    Y veo que el saldo general es -200 pesos


Escenario: Casos movimiento: Retirar cuenta de salida y cambiar cuenta de entrada en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_entrada"
    Y selecciono "nada" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que el movimiento "traspaso" no tiene cuenta de salida
    Y veo que "banco" no está entre las cuentas del movimiento "traspaso"
    Y veo que la cuenta de entrada del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es 200 pesos
    Y veo que el saldo general es 200 pesos


Escenario: Casos movimiento: Retirar cuenta de entrada y cambiar cuenta de salida y modificar importe en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "nada" en el campo "cta_entrada"
    Y selecciono "caja" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el movimiento "traspaso" no tiene cuenta de entrada
    Y veo que "efectivo" no está entre las cuentas del movimiento "traspaso"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es -150 pesos
    Y veo que el saldo general es -150 pesos


Escenario: Casos movimiento: Retirar cuenta de salida y cambiar cuenta de entrada y modificar importe en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_entrada"
    Y selecciono "nada" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que el movimiento "traspaso" no tiene cuenta de salida
    Y veo que "banco" no está entre las cuentas del movimiento "traspaso"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es 150 pesos
    Y veo que el saldo general es 150 pesos


Escenario: Casos movimiento: Intercambiar lugar de cuentas en movimiento de traspaso
    Dadas dos cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_entrada"
    Y selecciono "efectivo" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "banco"
    Y veo que la cuenta de salida del movimiento "traspaso" es "efectivo"
    Y veo que el saldo de Efectivo es -200 pesos
    Y veo que el saldo de Banco es 200 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Intercambiar lugar de cuentas y modificar importe en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_entrada"
    Y selecciono "efectivo" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "banco"
    Y veo que la cuenta de salida del movimiento "traspaso" es "efectivo"
    Y veo que el saldo de Efectivo es -150 pesos
    Y veo que el saldo de Banco es 150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Pasar cuenta de entrada a cuenta de salida y cambiar cuenta de entrada en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_entrada"
    Y selecciono "efectivo" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "caja"
    Y veo que la cuenta de salida del movimiento "traspaso" es "efectivo"
    Y veo que el saldo de Efectivo es -200 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es 200 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Pasar cuenta de salida a cuenta de entrada, cambiar cuenta de salida y modificar importe en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_entrada"
    Y selecciono "caja" en el campo "cta_salida"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "banco"
    Y veo que la cuenta de salida del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 200 pesos
    Y veo que el saldo de Caja es -200 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Pasar cuenta de entrada a cuenta de salida, cambiar cuenta de entrada y modificar importe en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "caja" en el campo "cta_entrada"
    Y selecciono "efectivo" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "caja"
    Y veo que la cuenta de salida del movimiento "traspaso" es "efectivo"
    Y veo que el saldo de Efectivo es -150 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo de Caja es 150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Pasar cuenta de salida a cuenta de entrada, cambiar cuenta de salida y modificar importe en movimiento de traspaso
    Dadas tres cuentas
    Y un movimiento con los siguientes valores
        | concepto | importe | cta_entrada | cta_salida |
        | traspaso | 200     | e           | b          |
    
    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_mod_mov"
    Y selecciono "banco" en el campo "cta_entrada"
    Y selecciono "caja" en el campo "cta_salida"
    Y escribo "150" en el campo "importe"
    Y cliqueo en el botón

    Entonces veo que la cuenta de entrada del movimiento "traspaso" es "banco"
    Y veo que la cuenta de salida del movimiento "traspaso" es "caja"
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 150 pesos
    Y veo que el saldo de Caja es -150 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Eliminar movimiento de entrada
    Dada una cuenta
    Y un movimiento con los siguientes valores:
        | concepto | importe | cta_entrada | cta_salida |
        | aSaldo   | 200     | e           |            |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_elim_mov"
    Y cliqueo en el botón de id "id_btn_confirm"

    Entonces veo 0 movimientos en la página
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Eliminar movimiento de salida
    Dada una cuenta
    Y un movimiento con los siguientes valores:
        | concepto | importe | cta_entrada | cta_salida |
        | aSaldo   | 200     |             | e          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_elim_mov"
    Y cliqueo en el botón de id "id_btn_confirm"

    Entonces veo 0 movimientos en la página
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo general es 0 pesos


Escenario: Casos movimiento: Eliminar movimiento de traspaso
    Dadas dos cuentas
    Y un movimiento con los siguientes valores:
        | concepto | importe | cta_entrada | cta_salida |
        | aSaldo   | 200     | e           | b          |

    Cuando voy a la página principal
    Y cliqueo en el botón de clase "link_elim_mov"
    Y cliqueo en el botón de id "id_btn_confirm"

    Entonces veo 0 movimientos en la página
    Y veo que el saldo de Efectivo es 0 pesos
    Y veo que el saldo de Banco es 0 pesos
    Y veo que el saldo general es 0 pesos
