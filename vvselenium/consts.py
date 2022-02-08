from selenium.webdriver.common.by import By

BYS = {
    'clase': By.CLASS_NAME,
    'class': By.CLASS_NAME,
    'id': By.ID,
    'selector css': By.CSS_SELECTOR,
    'contenido': By.LINK_TEXT,
}

CARDINALES = dict(
    un=1, uno=1, una=1, une=1,
    dos=2,
    tres=3,
    cuatro=4,
    cinco=5,
    seis=6,
    siete=7,
    ocho=8,
    nueve=9,
    diez=10,
)

ORDINALES = dict(
    primer=0, primero=0, primera=0, primere=0,
    segundo=1, segunda=1,
    tercer=2, tercero=2, tercera=2,
    cuarto=3, cuarta=3,
    quinto=4, quinta=4,
)

TERMINOS_TRUE = (
    'seleccionado', 'activado', 'habilitado', 'on', 'encendido', 'sí',
    'true', 'True',
)
TERMINOS_FALSE = (
    'deseleccionado', 'desactivado', 'deshabilitado', 'off', 'apagado',
    'no', 'false', 'False',
)
