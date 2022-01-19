from urllib.parse import urlparse

from django.urls import reverse

from behave import then
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from features.steps.consts_base import BYS, ORDINALES
from features.steps.helpers import espacios_a_snake, espera, tomar_atributo, \
    fijar_atributo


# FORMS Y CARGA DE DATOS

@then('veo un campo "{campo_name}" en el form de id "{form_id}"')
def veo_campo_en_form(context, campo_name, form_id):
    form = context.browser.esperar_elemento(f'id_form_{form_id}')
    try:
        campo = form.esperar_elemento(
            f'input[name="{campo_name}"]',
            By.CSS_SELECTOR
        )
    except NoSuchElementException:
        try:
            campo = form.esperar_elemento(
                f'select[name="{campo_name}"]',
                By.CSS_SELECTOR
            )
        except NoSuchElementException:
            raise NoSuchElementException(
                f'No se encontró ningún campo de nombre "{campo_name}".'
            )
    fijar_atributo(context, campo_name, campo)


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


@then('veo que el checkbox "{checkbox}" está {estado}')
def estado_checkbox(context, checkbox, estado):
    elemento = context.browser.esperar_elemento(checkbox, By.NAME)
    if estado == 'seleccionado':
        context.test.assertTrue(elemento.is_selected())
    elif estado == 'deseleccionado':
        context.test.assertFalse(elemento.is_selected())
    else:
        raise ValueError(f'No se acepta {estado}. '
                         f'Opciones válidas: seleccionado - deseleccionado')


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


@then('soy dirigido a la página principal')
def soy_dirigido_a(context):
    context.execute_steps('Entonces soy dirigido a la página "home"')


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


@then('veo un "{tag}" de {tipo} "{nombre}" con texto "{texto}"')
def elemento_tiene_texto(context, tag, tipo, nombre, texto):
    tipo = "class" if tipo == "clase" else tipo
    context.execute_steps(
        f'Entonces veo varios "{tag}" de {tipo} "{nombre}"'
    )
    elementos = tomar_atributo(context, f'{tipo}_{tag}_{nombre}')

    try:
        next(x for x in elementos if x.text == texto)
    except StopIteration:
        raise AssertionError(
            f'No se encontró un elemento "{tipo}_{tag}_{nombre}" '
            f'con texto "{texto}"'
        )


@then('veo una "{tag}" de {tipo} "{nombre}"')
def veo_tag(context, tag, tipo, nombre):
    context.execute_steps(f'Entonces veo un "{tag}" de {tipo} "{nombre}"')


@then('veo un "{tag}" de {tipo} "{nombre}"')
def elemento_aparece(context, tag, tipo, nombre):
    by = BYS.get(tipo, tipo)
    tipo = "class" if tipo == "clase" else tipo
    nombre_elemento = f'{tipo}_{tag}_{nombre}'

    elemento = context.browser.esperar_elemento(nombre_elemento, by)
    context.test.assertTrue(
        elemento.es_visible(), f"{nombre_elemento} no es visible")
    fijar_atributo(context, nombre_elemento, elemento)


@then('veo varios "{tag}" de {tipo} "{nombre}"')
def veo_varios_elementos(context, tag, tipo, nombre):
    by = BYS.get(tipo, tipo)
    tipo = "class" if tipo == "clase" else tipo
    nombre_elementos = f'{tipo}_{tag}_{nombre}'
    elementos = context.browser.esperar_elementos(nombre_elementos, by)
    fijar_atributo(context, nombre_elementos, elementos)


@then('veo varios elementos de clase "{clase}"')
def veo_varios_elementos(context, clase):
    elementos = context.browser.esperar_elementos(clase, By.CLASS_NAME)
    fijar_atributo(context, clase, elementos)


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


@then('veo una clase "{clase}"')
def veo_una_clase(context, clase):
    fijar_atributo(context, clase, context.browser.esperar_elementos(clase))


@then('veo un tag "{tag}" dentro de una clase "{clase}"')
def veo_un_tag_en_una_clase(context, tag, clase):
    elementos = context.browser.esperar_elementos(clase)

    for elemento in elementos:
        try:
            fijar_atributo(
                context,
                f'{clase}-{tag}',
                elemento.find_element_by_tag_name(tag)
            )
            return
        except NoSuchElementException:
            pass

    raise NoSuchElementException(
        f'No se encontró un tag "{tag}" '
        f'dentro de ningún elemento de clase "{clase}"'
    )


@then('veo que el elemento dado "{elemento}" '
      'incluye un "{tag}" de {tipo} "{nombre}" en la posición {pos}')
def veo_que_elemento_incluye(context, elemento, tag, tipo, nombre, pos):
    i = int(pos)-1
    tipo = "class" if tipo == "clase" else tipo
    nombre_contenidos = f'{tipo}_{tag}_{nombre}'

    context.execute_steps(
        f'Entonces veo que el elemento dado "{elemento}" incluye varios "{tag}"'
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

    fijar_atributo(context, f'{nombre_contenidos}_{pos}', contenidos[i])


@then('veo que el elemento dado "{elemento}" '
      'incluye un "{tag}" de {tipo} "{nombre}"')
def veo_que_elemento_incluye(context, elemento, tag, tipo, nombre):
    tipo = "class" if tipo == "clase" else tipo
    by = BYS.get(tipo, tipo)
    nombre_contenido = f'{tipo}_{tag}_{espacios_a_snake(nombre)}'
    contenedor = tomar_atributo(context, elemento)

    contenido = contenedor.esperar_elemento(nombre_contenido, by)
    fijar_atributo(context, nombre_contenido, contenido)


@then('veo que el elemento dado "{elemento}" '
      'incluye varios "{tag}" de clase "{clase}"')
def veo_que_elemento_incluye(context, elemento, tag, clase):
    nombre_contenidos = f'class_{tag}_{clase}'
    contenedor = tomar_atributo(context, elemento)

    contenidos = contenedor.esperar_elementos(nombre_contenidos, By.CLASS_NAME)
    fijar_atributo(context, nombre_contenidos, contenidos)


@then('veo que el elemento dado "{elemento}" incluye varios "{tag}"')
def veo_que_elemento_incluye(context, elemento, tag):
    nombre_tag = 'a' if tag == 'link' else tag
    contenedor = tomar_atributo(context, elemento)

    contenidos = contenedor.esperar_elementos(nombre_tag, By.TAG_NAME)
    fijar_atributo(context, f'tags_{tag}', contenidos)


@then('veo que el elemento dado "{elemento}" '
      'incluye {tantos} "{tag}" de clase "{clase}"')
def veo_que_elemento_incluye(context, elemento, tantos, tag, clase):
    context.execute_steps(
        f'Entonces veo que el elemento dado "{elemento}" '
        f'incluye varios "{tag}" de clase "{clase}"'
    )
    contenidos = tomar_atributo(context, f'class_{tag}_{clase}')

    context.test.assertEqual(len(contenidos), int(tantos))


@then('veo que el elemento dado "{elemento}" incluye el texto "{texto}"')
def veo_que_elemento_incluye_texto(context, elemento, texto):
    contenedor = tomar_atributo(context, elemento)
    context.test.assertIn(texto, contenedor.text)


@then('veo que el elemento dado "{elemento}" incluye {tantos} "{tag}"')
def veo_que_elemento_incluye(context, elemento, tantos, tag):
    context.execute_steps(
        f'Entonces veo que el elemento dado "{elemento}" '
        f'incluye varios "{tag}"'
    )
    contenidos = tomar_atributo(context, f'tags_{tag}')

    context.test.assertEqual(len(contenidos), int(tantos))


@then('veo que el "{tag}" de {tipo} "{nombre}" incluye el texto "{texto}"')
def veo_que_tag_incluye_texto(context, tag, tipo, nombre, texto):
    tipo = "class" if tipo == "clase" else tipo
    context.execute_steps(f'''
        Entonces veo un "{tag}" de {tipo} "{nombre}"
        Y veo que el elemento dado "{tipo}_{tag}_{nombre}" incluye el texto "{texto}"
    ''')


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


@then('veo un elemento de id "{id}" y clase "{clase}" dentro del elemento dado "{nombre}"')
def veo_elemento_en_elemento(context, id, clase, nombre):
    continente = tomar_atributo(context, nombre)
    elemento = continente.esperar_elemento(f'#{id}.{clase}', By.CSS_SELECTOR)
    fijar_atributo(context, f'{id}_{clase}', elemento)


@then('veo un elemento de id "{id}" y clase "{clase}"')
def veo_elemento(context, id, clase):
    elemento = context.browser.esperar_elemento(
        f'#{id}.{clase}', By.CSS_SELECTOR
    )
    fijar_atributo(context, f'{id}_{clase}', elemento)


@then('veo un elemento de {atributo_in} "{nombre_in}" '
      'dentro del {orden} elemento de {atributo_out} "{nombre_out}"')
def veo_elemento_en_elemento(
        context, atributo_in, nombre_in, orden, atributo_out, nombre_out):
    atrib_out = BYS.get(atributo_out, By.LINK_TEXT)
    atrib_in = BYS.get(atributo_in, By.LINK_TEXT)
    ord = ORDINALES[orden]

    continente = context.browser.esperar_elementos(nombre_out, atrib_out)[ord]
    contenido = continente.esperar_elemento(nombre_in, atrib_in)
    fijar_atributo(context, nombre_in, contenido)


@then('veo un elemento de {atributo} "{nombre}"')
def veo_elemento(context, atributo, nombre):
    atributo = BYS[atributo]
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


@then('no veo un elemento de {atributo_in} "{nombre_in}" '
      'dentro de ningún elemento de {atributo_out} "{nombre_out}"')
def elemento_no_aparece_en_ningun_elemento(
        context, atributo_in, nombre_in, atributo_out, nombre_out):
    # TODO: ¿no debería ser por default By.CLASS_NAME?
    atrib_out = BYS.get(atributo_out, By.LINK_TEXT)
    atrib_in = BYS.get(atributo_in, By.LINK_TEXT)

    continentes = context.browser.esperar_elementos(nombre_out, atrib_out)
    for ind, continente in enumerate(continentes):
        context.test.assertEqual(
            len(continente.esperar_elementos(nombre_in, atrib_in, fail=False)),
            0,
            f'Aparece elemento de {atributo_in} "{nombre_in}" que no debería '
            f'aparecer como hijo del elemento {ind} de {atributo_out} '
            f'"{nombre_out}"'
        )


@then('no veo un elemento de {atributo_in} "{nombre_in}" '
      'dentro del {orden} elemento de {atributo_out} "{nombre_out}"')
def elemento_no_aparece_en_elemento(
        context, atributo_in, nombre_in, orden, atributo_out, nombre_out):
    atrib_out = BYS.get(atributo_out, By.LINK_TEXT)
    atrib_in = BYS.get(atributo_in, By.LINK_TEXT)
    ord = ORDINALES[orden]

    continente = context.browser.esperar_elementos(nombre_out, atrib_out)[ord]
    context.test.assertEqual(
        len(continente.esperar_elementos(nombre_in, atrib_in, fail=False)),
        0,
        f'Aparece elemento de {atributo_in} "{nombre_in}" que no debería '
        f'aparecer como hijo del {orden} elemento de {atributo_out} '
        f'"{nombre_out}"'
    )


@then('no veo un elemento de id "{id}" y clase "{clase}"')
def elemento_no_aparece(context, id, clase):
    context.execute_steps(
        f'Entonces no veo un elemento de selector css "#{id}.{clase}"'
    )


@then('no veo un elemento de {atributo} "{nombre}"')
def elemento_no_aparece(context, atributo, nombre):
    atrib = BYS.get(atributo, By.LINK_TEXT)
    context.test.assertEqual(
        len(context.browser.esperar_elementos(nombre, atrib, fail=False)),
        0,
        f'Aparece elemento de {atributo} "{nombre}" que no debería aparecer'
    )


@then('el tamaño del elemento dado "{comparado}" '
      'es igual al tamaño del elemento dado "{patron}"')
def mismo_tamanio(context, comparado, patron):
    context.test.assertEqual(
        tomar_atributo(context, comparado).size,
        tomar_atributo(context, patron).size
    )


@then('veo que el elemento dado "{nombre_elemento}" '
      'ajusta su tamaño al de la pantalla')
def elemento_ajusta_a_pantalla(context, nombre_elemento):
    elemento = tomar_atributo(context, nombre_elemento)
    try:
        context.test.assertEqual(
            round(elemento.size['height']),
            round(context.browser.get_window_size()['height']),
            'La altura no coincide con la de la pantalla'
        )
    except AssertionError:
        context.test.assertEqual(
            round(elemento.size['width']),
            round(context.browser.get_window_size()['width']),
            'Ni ancho ni altura coinciden con las de la pantalla:\n'
            f'Altura: {elemento.size["height"]} '
            f'vs {context.browser.get_window_size()["height"]}\n'
            f'Ancho: {elemento.size["width"]} '
            f'vs {context.browser.get_window_size()["width"]}'
        )


@then('Veo que el tamaño del elemento dado "{atrib}" '
      'coincide con las medidas tomadas al elemento dado "{elemento_medido}"')
def medidas_coinciden(context, atrib, elemento_medido):
    context.test.assertEqual(
        tomar_atributo(context, atrib).size,
        tomar_atributo(context, f'{elemento_medido}_medidas')
    )


# LOGIN / LOGOUT
@then('se inicia una sesión con mi nombre')
def inicia_sesion(context):
    div = context.browser.esperar_elemento('id_div_login')
    context.test.assertIn(
        context.test_username, div.get_attribute('innerHTML'))


@then('se cierra la sesión')
def cierra_sesion(context):
    div = context.browser.esperar_elemento('id_div_login')
    context.test.assertNotIn(
        context.test_username, div.get_attribute('innerHTML'))


# MISC

@then('me detengo')
def detenerse(context):
    input()


@then('fallo')
def fallar(context):
    context.test.fail()
