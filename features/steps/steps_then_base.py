from urllib.parse import urlparse

from django.urls import reverse

from behave import then
from selenium.webdriver.common.by import By


# FORMS Y CARGA DE DATOS
from features.steps.consts import BYS
from features.steps.helpers import espacios_a_snake, espera


@then('veo que entre las opciones del campo "{campo}" figura "{opcion}"')
def select_muestra_opcion(context, campo, opcion):
    select = context.browser.esperar_elemento(f'id_{campo}')
    opciones = [x.text for x in select.find_elements_by_tag_name('option')]
    context.test.assertIn(opcion, opciones)


@then('veo que entre las opciones del campo "{campo}" figuran')
def select_muestra_opciones(context, campo):
    for fila in context.table:
        opcion = fila['nombre']
        context.execute_steps(
            f'entonces veo que entre las opciones del campo "{campo}" '
            f'figura "{opcion}"'
        )


@then('veo que entre las opciones del campo "{campo}" no figura "{opcion}"')
def select_muestra_opcion(context, campo, opcion):
    select = context.browser.esperar_elemento(f'id_{campo}')
    opciones = [x.text for x in select.find_elements_by_tag_name('option')]
    context.test.assertNotIn(opcion, opciones)


@then('veo que el campo "{campo}" está deshabilitado')
def campo_deshabilitado(context, campo):
    elemento = context.browser.esperar_elemento(campo, By.NAME)
    context.test.assertFalse(elemento.is_enabled())


#  NAVEGACION

@then('soy dirigido a la página "{pagina}"')
def soy_dirigido_a(context, pagina):
    pagina = espacios_a_snake(pagina)
    espera(
        lambda: context.test.assertURLEqual(
            reverse(pagina),
            urlparse(context.browser.current_url).path
        )
    )


# ELEMENTOS

@then('no veo un elemento de {atributo} "{elemento}"')
def elemento_no_aparece(context, atributo, elemento):
    atr = BYS.get(atributo, By.LINK_TEXT)
    context.test.assertEqual(
        len(context.browser.esperar_elementos(elemento, atr, fail=False)), 0,
        f'Aparece elemento de {atributo} "{elemento}" que no debería aparecer'
    )


@then('veo un botón de {texto}')
def veo_un_boton(context, texto):
    context.browser.esperar_elemento(texto, By.LINK_TEXT)


@then('veo un formulario de {elem}')
def veo_formulario(context, elem):
    context.browser.esperar_elemento(f'id_form_{elem}')


@then('veo un mensaje de error: "{mensaje}"')
def veo_mensaje_de_error(context, mensaje):
    errores = context.browser.esperar_elemento('id_errores').text
    context.test.assertIn(mensaje, errores)


# MISC

@then('me detengo')
def detenerse(context):
    input()
