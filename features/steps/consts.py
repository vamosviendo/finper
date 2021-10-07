from selenium.webdriver.common.by import By

BYS = {
    'clase': By.CLASS_NAME,
    'id': By.ID,
    'selector css': By.CSS_SELECTOR,
    'contenido': By.LINK_TEXT,
}

LISTAS_DE_ENTIDADES = dict(
    movimiento='class_row_mov', movimientos='class_row_mov',
    cuenta='class_div_cuenta', cuentas='class_div_cuenta',
    titular='class_link_titular', titulares='class_link_titular',
)

ORDINALES = dict(
    primer=0, primero=0, primera=0,
    segundo=1, segunda=1,
    tercero=2, tercera=2,
    cuarto=3, cuarta=3,
    quinto=4, quinta=4,
)

# TODO: reemplazar esto por títulos en páginas (?)
NOMBRES_URL = {
    'modificar movimiento': 'mov_mod',
}
