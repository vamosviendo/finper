from django.urls import reverse

from behave import when
from selenium.webdriver.common.by import By

from consts import BYS, ORDINALES


@when('cliqueo en el {orden} botón de {atributo} "{texto}"')
def cliquear_en(context, orden, atributo, texto):
    atr = BYS.get(atributo, By.LINK_TEXT)
    context.browser.esperar_elementos(texto, atr)[ORDINALES[orden]].click()


@when('cliqueo en el botón de {atributo} "{texto}"')
def cliquear_en(context, atributo, texto):
    context.execute_steps(
        f'Cuando cliqueo en el primer botón de {atributo} "{texto}"'
    )


@when('cliqueo en el botón "{texto}"')
def cliquear_en_el_boton(context, texto):
    context.execute_steps(
        f'Cuando cliqueo en el botón de contenido "{texto}"'
    )


@when('cliqueo en el botón')
def cliquear_en(context):
    context.execute_steps(
        'Cuando cliqueo en el botón de id "id_btn_submit"'
    )


@when('{accion} "{texto}" en el campo "{campo}"') # acción=escribo, selecciono
def completar_campo(context, accion, texto, campo):
    if accion == 'escribo':
        tipo = 'input'
    elif accion == 'selecciono':
        texto = '---------' if texto == 'nada' else texto
        tipo = 'select'
    else:
        raise ValueError('La acción debe ser "escribo" o "selecciono')
    context.browser.completar(f'{tipo}[name="{campo}"]', texto, By.CSS_SELECTOR)


@when('voy a la página principal')
def ir_a_pag_principal(context):
    context.browser.get(context.get_url('/'))


@when('voy a la página "{nombre}"')
def ir_a_pag(context, nombre):
    context.browser.get(context.get_url(reverse(nombre)))


@when('me detengo')
def detenerse(context):
    input()
