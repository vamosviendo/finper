from urllib.parse import urlparse

from django.urls import reverse

from behave import then
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from features.steps.consts_base import BYS
from features.steps.helpers import espacios_a_snake, espera, tomar_atributo, \
    fijar_atributo


# FORMS Y CARGA DE DATOS

@then('veo que entre las opciones del campo "{campo}" figura "{opcion}"')
def select_muestra_opcion(context, campo, opcion):
    try:
        select = context.browser.esperar_elemento(f'id_{campo}')
    except NoSuchElementException:
        select = context.browser.esperar_elemento(f'id_select_{campo}')
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
    try:
        select = context.browser.esperar_elemento(f'id_{campo}')
    except NoSuchElementException:
        select = context.browser.esperar_elemento(f'id_select_{campo}')
    opciones = [x.text for x in select.find_elements_by_tag_name('option')]
    context.test.assertNotIn(opcion, opciones)


@then('veo que el campo "{campo}" está deshabilitado')
def campo_deshabilitado(context, campo):
    elemento = context.browser.esperar_elemento(campo, By.NAME)
    context.test.assertFalse(elemento.is_enabled())


#  NAVEGACION

@then('soy dirigido a la página "{pagina}" con el argumento "{argumento}"')
def soy_dirigido_a(context, pagina, argumento):
    pagina = espacios_a_snake(pagina)
    espera(
        lambda: context.test.assertURLEqual(
            reverse(pagina, args=[argumento]),
            urlparse(context.browser.current_url).path
        )
    )


@then('soy dirigido a la página principal')
def soy_dirigido_a(context):
    context.execute_steps('Entonces soy dirigido a la página "home"')


@then('soy dirigido a la página "{pagina}" con los argumentos')
def soy_dirigido_a(context, pagina):
    pagina = espacios_a_snake(pagina)
    args = [row['argumento'] for row in context.table]
    espera(
        lambda: context.test.assertURLEqual(
            reverse(pagina, args=args),
            urlparse(context.browser.current_url).path
        )
    )


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

@then('veo un mensaje de error: "{mensaje}"')
def veo_mensaje_de_error(context, mensaje):
    errores = context.browser.esperar_elemento('id_errores').text
    context.test.assertIn(mensaje, errores)


@then('veo un "{tag}" de {tipo} "{nombre}"')
def elemento_aparece(context, tag, tipo, nombre):
    by = BYS.get(tipo, tipo)
    tipo = "class" if tipo == "clase" else tipo
    nombre_elemento = f'{tipo}_{tag}_{nombre}'

    elemento = context.browser.esperar_elemento(nombre_elemento, by)
    context.test.assertTrue(
        elemento.es_visible(), f"{nombre_elemento} no es visible")
    fijar_atributo(context, nombre_elemento, elemento)


@then('veo un link de texto "{texto}"')
def veo_un_link(context, texto):
    nombre = f'a_text_{espacios_a_snake(texto)}'
    elemento = context.browser.esperar_elemento(texto, By.LINK_TEXT)
    fijar_atributo(context, nombre, elemento)


@then('veo un menú de {tipo} "{menu}"')
def veo_un_menu(context, tipo, menu):
    context.execute_steps(f'Entonces veo un "nav" de {tipo} "{menu}"')


@then('veo un menú "{menu}"')
def veo_un_menu(context, menu):
    context.execute_steps(f'Entonces veo un menú de id "{menu}"')


@then('veo que el elemento "{elemento}" '
      'incluye un "{tag}" de {tipo} "{nombre}" en la posición {pos}')
def veo_que_elemento_incluye(context, elemento, tag, tipo, nombre, pos):
    i = int(pos)-1
    tipo = "class" if tipo == "clase" else tipo
    nombre_contenidos = f'{tipo}_{tag}_{nombre}'

    context.execute_steps(
        f'Entonces veo que el elemento "{elemento}" incluye varios "{tag}"'
    )
    contenidos = tomar_atributo(context, f'tags_{tag}')
    context.test.assertTrue(
        len(contenidos) >= int(pos),
        f"No hay {pos} {nombre_contenidos}s en {elemento}. "
        f"Hay solamente {len(contenidos)}"
    )
    context.test.assertIn(
        nombre_contenidos,
        contenidos[i].get_attribute(tipo)
    )

    setattr(context, f'{nombre_contenidos}_{pos}', contenidos[i])


@then('veo que el elemento "{elemento}" '
      'incluye un "{tag}" de {tipo} "{nombre}"')
def veo_que_elemento_incluye(context, elemento, tag, tipo, nombre):
    tipo = "class" if tipo == "clase" else tipo
    by = BYS.get(tipo, tipo)
    nombre_contenido = f'{tipo}_{tag}_{espacios_a_snake(nombre)}'
    contenedor = tomar_atributo(context, elemento)

    contenido = contenedor.esperar_elemento(nombre_contenido, by)
    fijar_atributo(context, nombre_contenido, contenido)


@then('veo que el elemento "{elemento}" '
      'incluye varios "{tag}" de clase "{clase}"')
def veo_que_elemento_incluye(context, elemento, tag, clase):
    nombre_contenidos = f'class_{tag}_{clase}'
    contenedor = tomar_atributo(context, elemento)

    contenidos = contenedor.esperar_elementos(nombre_contenidos, By.CLASS_NAME)
    fijar_atributo(context, nombre_contenidos, contenidos)


@then('veo que el elemento "{elemento}" incluye varios "{tag}"')
def veo_que_elemento_incluye(context, elemento, tag):
    nombre_tag = 'a' if tag == 'link' else tag
    contenedor = tomar_atributo(context, elemento)

    contenidos = contenedor.esperar_elementos(nombre_tag, By.TAG_NAME)
    fijar_atributo(context, f'tags_{tag}', contenidos)


@then('veo que el elemento "{elemento}" '
      'incluye {tantos} "{tag}" de clase "{clase}"')
def veo_que_elemento_incluye(context, elemento, tantos, tag, clase):
    context.execute_steps(
        f'Entonces veo que el elemento "{elemento}" '
        f'incluye varios "{tag}" de clase "{clase}"'
    )
    contenidos = tomar_atributo(context, f'class_{tag}_{clase}')

    context.test.assertEqual(len(contenidos), int(tantos))


@then('veo que el elemento "{elemento}" incluye {tantos} "{tag}"')
def veo_que_elemento_incluye(context, elemento, tantos, tag):
    context.execute_steps(
        f'Entonces veo que el elemento "{elemento}" incluye varios "{tag}"'
    )
    contenidos = tomar_atributo(context, f'tags_{tag}')

    context.test.assertEqual(len(contenidos), int(tantos))


@then('veo que entre los "{tag}" de clase "{clase}" '
      'está el de {atributo} "{valor}"')
def entre_elementos_esta_el_elemento(context, tag, clase, atributo, valor):
    elementos = context.browser.esperar_elementos(
        f'class_{tag}_{clase}', fail=False)

    context.test.assertIn(
        valor,
        [x.get_attribute(atributo) for x in elementos]
    )


@then('veo que entre los "{tag}" de clase "{clase}" '
      'no está el de {atributo} "{valor}"')
def entre_elementos_no_esta_el_elemento(context, tag, clase, atributo, valor):
    elementos = context.browser.esperar_elementos(
        f'class_{tag}_{clase}', fail=False)

    context.test.assertNotIn(
        valor,
        [x.get_attribute(atributo) for x in elementos]
    )


@then('veo un botón de {texto}')
def veo_un_boton(context, texto):
    context.browser.esperar_elemento(texto, By.LINK_TEXT)


@then('veo un formulario de {elem}')
def veo_formulario(context, elem):
    context.browser.esperar_elemento(f'id_form_{elem}')


@then('veo un elemento de {atributo} "{nombre}"')
def veo_elemento(context, atributo, nombre):
    atributo = "class_name" if atributo == "clase" else atributo
    elemento = context.browser.esperar_elemento(nombre, atributo)
    fijar_atributo(context, nombre, elemento)


@then('no veo un "{tag}" de {tipo} "{nombre}"')
def elemento_no_aparece(context, tag, tipo, nombre):
    by = BYS.get(tipo, tipo)
    tipo = "class" if tipo == "clase" else tipo
    nombre_elemento = f'{tipo}_{tag}_{nombre}'

    try:
        elemento = context.browser.esperar_elemento(nombre_elemento, by)
    except NoSuchElementException:
        return

    context.test.assertFalse(elemento.es_visible())


@then('no veo un menú de {tipo} "{menu}"')
def menu_no_aparece(context, tipo, menu):
    context.execute_steps(f'Entonces no veo un "nav" de {tipo} "{menu}"')


@then('no veo un menú "{menu}"')
def menu_no_aparece(context, menu):
    context.execute_steps(f'Entonces no veo un menú de id "{menu}"')


@then('no veo un elemento de {atributo} "{nombre}"')
def elemento_no_aparece(context, atributo, nombre):
    atr = BYS.get(atributo, By.LINK_TEXT)
    context.test.assertEqual(
        len(context.browser.esperar_elementos(nombre, atr, fail=False)), 0,
        f'Aparece elemento de {atributo} "{nombre}" que no debería aparecer'
    )


@then('el tamaño del elemento "{comparado}" '
      'es igual al tamaño del elemento "{patron}"')
def mismo_tamanio(context, comparado, patron):
    context.test.assertEqual(
        tomar_atributo(context, comparado).size,
        tomar_atributo(context, patron).size
    )


# MISC

@then('me detengo')
def detenerse(context):
    input()
