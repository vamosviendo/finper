from datetime import date

from behave import given, then, when
from selenium.webdriver.common.by import By

from diario.models import Cuenta, Movimiento


# @givens

@given('una cuenta con los siguientes valores')
def hay_una_cuenta(context):
    for fila in context.table:
        cuenta = Cuenta.crear(fila['nombre'], fila['slug'])
        saldo = fila.get('saldo')
        if saldo and float(saldo) != 0.0:
            Movimiento.crear(
                concepto='Saldo al inicio',
                importe=saldo,
                cta_entrada=cuenta,
            )


# @whens (por orden alfabético)

@when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
def agregar_cuenta(context, nombre, slug):
    context.browser.completar('id_nombre', nombre)
    if slug is None: slug = 'E'
    context.browser.completar('id_slug', slug)
    context.browser.pulsar()


@when('agrego un movimiento con campos')
def agregar_movimiento(context):
    for fila in context.table:
        context.browser.completar(f"id_{fila['nombre']}", fila['valor'])
    context.browser.pulsar()


@when('cliqueo en el botón {texto}')
def cliquear_en_el_boton(context, texto):
    context.browser.esperar_elemento(texto, By.LINK_TEXT).click()


@when('completo el form de dividir cuenta con estos valores')
def completar_form_dividir_cuenta(context):
    for ind, fila in enumerate(context.table):
        context.browser.completar(f'id_form-{ind}-nombre', fila['nombre'])
        context.browser.completar(f'id_form-{ind}-slug', fila['slug'])
        context.browser.completar(f'id_form-{ind}-saldo', fila['saldo'])
    context.browser.pulsar()


@when('voy a la página principal')
def ir_a_pag_principal(context):
    context.browser.get(context.get_url('/'))


# @thens (por orden alfabético)

@then('el campo "{campo}" del formulario tiene fecha de hoy como valor por defecto')
def campo_muestra_fecha_de_hoy(context, campo):
    campo_fecha = context.browser.esperar_elemento(f'id_{campo}')
    context.test.assertEqual(
        campo_fecha.get_attribute("value"),
        date.today().strftime('%Y-%m-%d')
    )


@then('la cuenta "{slug}" tiene saldo {monto}')
def cuenta_tiene_saldo(context, slug, monto):
    cuenta = context.browser.esperar_elemento(f'id_div_cta_{slug.lower()}')
    context.test.assertEqual(
        cuenta.find_element_by_class_name('class_saldo_cuenta').text,
        monto
    )


@then('la grilla de cuentas está vacia')
def grilla_cuentas_vacia(context):
    cuentas = context.browser.esperar_elementos('class_div_cuenta', fail=False)
    context.test.assertEqual(len(cuentas), 0)


@then('la lista de movimientos está vacia')
def lista_movimientos_vacia(context):
    movs = context.browser.esperar_elementos('tr', By.TAG_NAME)
    context.test.assertEqual(len(movs), 1)


@then('las subcuentas de la página de {cuenta} tienen estos valores')
def subcuentas_de_detalle_cuenta_coinciden_con(context, cuenta):
    nombres = [e.text for e in
               context.browser.esperar_elementos('class_nombre_cuenta')]
    saldos = [e.text for e in
              context.browser.esperar_elementos('class_saldo_cuenta')]
    ids = [e.get_attribute('id') for e in
           context.browser.esperar_elementos('class_div_subcta')]

    for i, fila in enumerate(context.table):
        context.test.assertEqual(
            ids[i], f"id_div_cta_{fila['slug']}",
            f"La id id_div_cta_{fila['slug']} no coincide con {ids[i]}"
        )
        context.test.assertEqual(
            nombres[i], fila['nombre'],
            f"El nombre {fila['nombre']} no coincide con {nombres[i]}."
        )
        saldo = f"{float(fila['saldo']):.2f}"
        context.test.assertEqual(
            saldos[i], saldo,
            f"El saldo de {fila['nombre']} es {saldos[i]}, no {saldo}."
        )


@then('los movimientos en la página tienen estos valores')
def movs_en_pagina_coinciden_con(context):
    conceptos = [e.text for e in
                 context.browser.esperar_elementos('class_td_concepto')]
    importes = [e.text for e in
                context.browser.esperar_elementos('class_td_importe')]
    cuentas = [e.text for e in
               context.browser.esperar_elementos('class_td_cuentas')]

    for i, fila in enumerate(context.table):
        context.test.assertEqual(
            conceptos[i], fila['concepto'],
            f"El concepto {fila['concepto']} no coincide con {conceptos[i]}"
        )
        importe = f"{float(fila['importe']):.2f}"
        context.test.assertEqual(
            importes[i], importe,
            f"El importe del mov {i+1} es {importes[i]}, no {importe}"
        )
        context.test.assertEqual(
            cuentas[i], fila['cuentas'],
            f"Las cuentas involucradas en el mov {i+1} son {cuentas[i]}, "
            f"no {fila['cuentas']}"
        )


@then('veo {num} movimient{os} en la página')
def veo_movimiento(context, num, os):
    if num == 'un':
        num = 1
    else:
        num = int(num)

    lista_ult_movs = context.browser.esperar_elemento('id_lista_ult_movs')
    ult_movs = lista_ult_movs.find_elements_by_tag_name('tr')

    context.test.assertEqual(len(ult_movs), num+1)  # El encabezado y un movimiento


@then('veo {x} subcuentas en la página {cuenta}')
def detalle_cuenta_tiene_subcuentas(context, cuenta, x):
    nombre_cta_main = context.browser.esperar_elemento(
        'class_nombre_cuenta_main', By.CLASS_NAME)

    context.test.assertEqual(
        nombre_cta_main.text, cuenta,
        f'La cuenta seleccionada no coincide con {cuenta}'
    )

    num_subcuentas = len(context.browser.esperar_elementos('class_div_subcta'))
    context.test.assertEqual(
        num_subcuentas, int(x),
        f'La página {cuenta} mustra {num_subcuentas} subcuentas, no {x}.'
    )


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


@then('veo una cuenta en la grilla con nombre "{nombre}"')
def veo_una_cuenta(context, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertEqual(len(cuentas), 1)
    context.test.assertEqual(
        cuentas[0].find_element_by_class_name('class_nombre_cuenta').text,
        nombre
    )


@then('veo un botón de {texto}')
def veo_un_boton(context, texto):
    context.browser.esperar_elemento(texto, By.LINK_TEXT)


@then('veo un formulario de {elem}')
def veo_formulario(context, elem):
    context.browser.esperar_elemento(f'id_form_{elem}')
