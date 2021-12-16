from random import randrange

from django.urls import reverse

from behave import when
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from consts_base import BYS, ORDINALES
from features.steps.helpers import tomar_atributo, fijar_atributo


@when('cliqueo en el {orden} botón de texto "{texto}"')
def cliquear_en(context, orden, texto):
    botones = context.browser.esperar_elementos(
        f'//button[normalize-space()="{texto}"]', By.XPATH)
    botones[ORDINALES[orden]].click()


@when('cliqueo en el botón de texto "{texto}"')
def cliquear_en(context, texto):
    context.execute_steps(
        f'Cuando cliqueo en el primer botón de texto "{texto}"'
    )


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
        f'Cuando cliqueo en el botón de texto "{texto}"'
    )


@when('cliqueo en el botón')
def cliquear_en(context):
    context.execute_steps(
        'Cuando cliqueo en el botón de id "id_btn_submit"'
    )


@when('cliqueo en el link de texto "{texto}"')
def cliquear_en(context, texto):
    context.browser.esperar_elemento(texto, By.LINK_TEXT).click()


@when('cliqueo en la opción "{opcion}" del {orden} menú de {tipo} "{menu}"')
def cliquear_en_opcion(context, opcion, orden, tipo, menu):
    tipo = "class" if tipo == "clase" else tipo

    context.execute_steps(f'''
        Entonces veo varios "nav" de {tipo} "{menu}"
        Cuando cliqueo en la opción "{opcion}" del {orden} elemento dado "{tipo}_nav_{menu}"
    ''')


@when('cliqueo en la opción "{opcion}" del menú de {tipo} "{menu}"')
def cliquear_en_opcion(context, opcion, tipo, menu):
    tipo = "class" if tipo == "clase" else tipo
    context.execute_steps(f'''
        Entonces veo un menú de {tipo} "{menu}"
        Cuando cliqueo en la opción "{opcion}" del elemento dado "{tipo}_nav_{menu}"        
    ''')


@when('cliqueo en la opción "{opcion}" del menú "{menu}"')
def cliquear_en_opcion(context, opcion, menu):
    context.execute_steps(
        f'Cuando cliqueo en la opción "{opcion}" del menú de id "{menu}"')


@when('cliqueo en la opción "{opcion}" del {orden} elemento dado "{nombre}"')
def cliquear_en_opcion_de_elemento(context, opcion, orden, nombre):
    menues = tomar_atributo(context, nombre)
    indice = ORDINALES[orden]
    fijar_atributo(context, f'{nombre}_{indice}', menues[indice])
    context.execute_steps(
        f'Cuando cliqueo en la opción "{opcion}" del elemento dado "{nombre}_{indice}"'
    )


@when('cliqueo en la opción "{opcion}" del {orden} elemento "{nombre}"')
def cliquear_en_opcion_de_elemento(context, opcion, orden, nombre):
    context.execute_steps(f'''
        Entonces veo varios elementos de clase "{nombre}"
        Cuando cliqueo en la opción "{opcion}" del {orden} elemento dado "{nombre}"
    ''')


@when('cliqueo en la opción "{opcion}" del elemento dado "{nombre}"')
def cliquear_en_opcion(context, opcion, nombre):
    menu = tomar_atributo(context, nombre)
    try:
        opcion = menu.find_element_by_link_text(opcion)
    except NoSuchElementException:
        opcion = menu.esperar_enlace_con_titulo(opcion)
    opcion.click()


@when('cliqueo en el elemento dado "{elemento}"')
def cliquear_en_elemento_dado(context, elemento):
    tomar_atributo(context, elemento).click()


@when('cliqueo en el "{tag}" de id "{id}"')
def cliquear_en(context, tag, id):
    context.browser.esperar_elemento(f'id_{tag}_{id}').click()


@when('cliqueo en un "{tag}" de clase "{clase}"')
def cliquear_en(context, tag, clase):
    context.browser.esperar_elemento(f'class_{tag}_{clase}', By.CLASS_NAME)\
        .click()


@when('cliqueo en el {orden} "{tag}" de clase "{clase}"')
def cliquear_en(context, orden, tag, clase):
    indice = ORDINALES[orden]
    context.browser.esperar_elementos(f'class_{tag}_{clase}')[indice].click()


@when('cliqueo en el "{tag}" de clase "{clase}" con {atributo} "{valor}"')
def cliquear_en(context, tag, clase, atributo, valor):
    elementos = context.browser.esperar_elementos(f'class_{tag}_{clase}')
    if atributo == "href":
        if not valor.startswith('/'):
            valor = f'/{valor}'
        valor = f'{context.test.live_server_url}{valor}'
        print(valor)
        print([x.get_attribute("href") for x in elementos])

    next(x for x in elementos if x.get_attribute(atributo) == valor).click()


@when('elijo al azar y guardo un elemento de clase "{clase}"')
def elegir_y_guardar(context, clase):
    elementos = context.browser.esperar_elementos(clase)
    indice = randrange(len(elementos))
    elegido = elementos[indice]
    fijar_atributo(context, clase, elegido)
    fijar_atributo(context, 'indice', indice)


@when('elijo al azar un elemento de clase "{clase}" '
      'y guardo su atributo "{atributo}"')
def elegir_y_guardar_atributo(context, clase, atributo):
    context.execute_steps(
        f'Cuando elijo al azar y guardo un elemento de clase {clase}'
    )
    elemento = tomar_atributo(context, clase)
    fijar_atributo(
        context,
        f'{clase}_{atributo}',
        elemento.get_attribute(atributo)
    )


@when('completo y envío el formulario de login')
def ingresar_nombre_y_password(context):
    context.execute_steps(f'''
        Cuando ingreso el nombre de usuario
        Y ingreso el password
        Y cliqueo en el botón de id "id_btn_login"
    ''')


@when('ingreso el nombre de usuario')
def ingresar_nombre(context):
    context.execute_steps(
        f'Cuando escribo "{context.test_username}" en el campo "username"')


@when('ingreso el password')
def ingresar_password(context):
    context.execute_steps(
        f'Cuando escribo "{context.test_password}" en el campo "password"')


@when('{accion} "{texto}" en el campo "{campo}"') # acción=escribo, selecciono
def completar_campo(context, accion, texto, campo):
    if accion == 'escribo':
        try:
            context.browser.completar(
                f'input[name="{campo}"]', texto, By.CSS_SELECTOR)
        except NoSuchElementException:
            try:
                context.browser.completar(
                    f'textarea[name="{campo}"]', texto, By.CSS_SELECTOR)
            except NoSuchElementException:
                raise NoSuchElementException(
                    f'No se encontró campo de texto ni textarea '
                    f'con nombre "{campo}"'
                )
    elif accion == 'selecciono':
        texto = '---------' if texto == 'nada' else texto
        context.browser.completar(
            f'select[name="{campo}"', texto, By.CSS_SELECTOR)
    else:
        raise ValueError('La acción debe ser "escribo" o "selecciono')


@when('tomo las medidas del elemento dado "{nombre_elemento}"')
def tomar_medidas(context, nombre_elemento):
    elemento = tomar_atributo(context, nombre_elemento)
    fijar_atributo(context, f'{nombre_elemento}_medidas', elemento.size)


@when('voy a la página principal')
def ir_a_pag_principal(context):
    context.browser.get(context.get_url('/'))


@when('voy a la página "{nombre}" con el argumento "{arg}"')
def ir_a_pag(context, nombre, arg):
    context.browser.get(context.get_url(reverse(nombre, args=[arg])))


@when('voy a la página "{nombre}" con los argumentos')
def ir_a_pag(context, nombre):
    args = [row['argumento'] for row in context.table]
    context.browser.get(context.get_url(reverse(nombre, args=args)))


@when('voy a la página "{nombre}"')
def ir_a_pag(context, nombre):
    context.browser.get(context.get_url(reverse(nombre)))


@when('me detengo')
def detenerse(context):
    input()


@when('fallo')
def fallar(context):
    context.test.fail()
