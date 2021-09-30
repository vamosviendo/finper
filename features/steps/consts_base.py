from selenium.webdriver.common.by import By

BYS = {
    'clase': By.CLASS_NAME,
    'class': By.CLASS_NAME,
    'id': By.ID,
    'selector css': By.CSS_SELECTOR,
    'contenido': By.LINK_TEXT,
}

ORDINALES = dict(
    primer=0, primero=0, primera=0,
    segundo=1, segunda=1,
    tercero=2, tercera=2,
    cuarto=3, cuarta=3,
    quinto=4, quinta=4,
)
