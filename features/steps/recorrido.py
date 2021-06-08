from datetime import date

from behave import then, when
from selenium.webdriver.common.by import By

from diario.models import Cuenta


@when('voy a la pagina principal')
def ir_a_pag_principal(context):
    context.browser.get(context.get_url('/'))


@then('veo que el saldo {nombre} es {tantos} pesos')
def el_saldo_general_es_tanto(context, nombre, tantos):
    if nombre == 'general':
        total = context.browser.esperar_elemento('id_importe_saldo_gral')
    else:
        nombre = nombre[3:]
        slug = Cuenta.tomar(nombre=nombre).slug
        total = context.browser.esperar_elemento(f'id_saldo_cta_{slug}')

    if tantos == 'cero':
        tantos = '0.00'
    elif tantos.find('.') == -1:
        tantos += '.00'

    context.test.assertEqual(
        total.text, tantos
    )


@then('la grilla de cuentas está vacia')
def grilla_cuentas_vacia(context):
    cuentas = context.browser.esperar_elementos('class_div_cuenta', fail=False)
    context.test.assertEqual(len(cuentas), 0)


@then('la lista de movimientos está vacia')
def lista_movimientos_vacia(context):
    movs = context.browser.esperar_elementos('tr', By.TAG_NAME)
    context.test.assertEqual(len(movs), 1)


@then('veo un botón de {texto}')
def veo_un_boton(context, texto):
    context.browser.esperar_elemento(texto, By.LINK_TEXT)


@when('cliqueo en el botón {texto}')
def cliquear_en_el_boton(context, texto):
    context.browser.esperar_elemento(texto, By.LINK_TEXT).click()


@then('veo un formulario de {elem}')
def veo_formulario(context, elem):
    context.browser.esperar_elemento(f'id_form_{elem}')


@when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
def agregar_cuenta(context, nombre, slug):
    context.browser.completar('id_nombre', nombre)
    if slug is None: slug = 'E'
    context.browser.completar('id_slug', slug)
    context.browser.pulsar()


@then('veo una cuenta en la grilla con nombre "{nombre}"')
def veo_una_cuenta(context, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertEqual(len(cuentas), 1)
    context.test.assertEqual(
        cuentas[0].find_element_by_class_name('class_nombre_cuenta').text,
        nombre
    )


@then('la cuenta "{slug}" tiene saldo {monto}')
def cuenta_tiene_saldo(context, slug, monto):
    cuenta = context.browser.esperar_elemento(f'id_div_cta_{slug.lower()}')
    context.test.assertEqual(
        cuenta.find_element_by_class_name('class_saldo_cuenta').text,
        monto
    )


@then('el campo "{campo}" del formulario tiene fecha de hoy como valor por defecto')
def campo_muestra_fecha_de_hoy(context, campo):
    campo_fecha = context.browser.esperar_elemento(f'id_{campo}')
    context.test.assertEqual(
        campo_fecha.get_attribute("value"),
        date.today().strftime('%Y-%m-%d')
    )


@when('agrego un movimiento con campos')
def agregar_movimiento(context):
    for fila in context.table:
        context.browser.completar(f"id_{fila['nombre']}", fila['valor'])
    context.browser.pulsar()


@then('veo un movimiento en la página')
def veo_movimiento(context):
    lista_ult_movs = context.browser.esperar_elemento('id_lista_ult_movs')
    ult_movs = lista_ult_movs.find_elements_by_tag_name('tr')
    context.test.assertEqual(len(ult_movs), 2)  # El encabezado y un movimiento
