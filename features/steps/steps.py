""" Las implementaciones deben ir de lo más particular a lo más general.
    Por ejemplo:
        @when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
        @when('agrego una cuenta con nombre "{nombre}"')
        @when('agrego una cuenta')
"""

from datetime import date

from behave import given, then, when
from selenium.webdriver.common.by import By

from diario.models import Cuenta, Movimiento
from utils.constantes import ORDINALES


def table_to_str(tabla):
    result = ''
    if tabla.headings:
        result = '|'
    for enc in tabla.headings:
        result += enc + '|'
    result += '\n'
    for fila in tabla.rows:
        if fila.cells:
            result += '|'
        for cell in fila.cells:
            result += cell + '|'
        result += '\n'
    return result


# @givens

@given('{n} cuentas con los siguientes valores')
def hay_n_cuentas(context, n):
    for fila in context.table:
        cuenta = Cuenta.crear(fila['nombre'], fila['slug'])
        saldo = fila.get('saldo')
        if saldo and float(saldo) != 0.0:
            Movimiento.crear(
                concepto='Saldo al inicio',
                importe=saldo,
                cta_entrada=cuenta,
            )


@given('{n} movimientos con los siguientes valores')
def hay_n_movimientos(context, n):
    for fila in context.table:
        slug_entrada = fila.get('cta_entrada')
        slug_salida = fila.get('cta_salida')
        cta_entrada = cta_salida = None

        if slug_entrada:
            cta_entrada = Cuenta.tomar(slug=slug_entrada)
        if slug_salida:
            cta_salida = Cuenta.tomar(slug=slug_salida)

        Movimiento.crear(
            concepto=fila['concepto'],
            importe=fila['importe'],
            cta_entrada=cta_entrada,
            cta_salida=cta_salida,
        )


@given('una cuenta con los siguientes valores')
def hay_una_cuenta(context):
    context.execute_steps(
        'Dadas 1 cuentas con los siguientes valores\n ' +
        table_to_str(context.table)
    )


@given('una cuenta')
def hay_una_cuenta(context):
    context.execute_steps(
        'Dada una cuenta con los siguientes valores\n' +
        '| nombre   | slug |\n' +
        '| Efectivo | e    |'
    )


@given('la cuenta "{nombre}" dividida en subcuentas')
def cuenta_dividida(context, nombre):
    cta = Cuenta.tomar(nombre=nombre)
    subcuentas = list()
    for fila in context.table:
        subcuentas.append(dict(
                nombre=fila['nombre'],
                slug=fila['slug'],
                saldo=int(fila['saldo'])
        ))
    cta.dividir_entre(*subcuentas)


@given('movimientos con estos valores')
def hay_n_movimientos(context):
    for fila in context.table:
        ce = cs = None
        if fila.get('cta_entrada') is not None:
            ce = Cuenta.tomar(slug=fila.get('cta_entrada'))
        if fila.get('cta_salida') is not None:
            cs = Cuenta.tomar(slug=fila.get('cta_salida'))
        Movimiento.crear(
            concepto=fila['concepto'],
            importe=fila['importe'],
            cta_entrada=ce,
            cta_salida=cs,
        )


# @whens (por orden alfabético)

@when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
def agregar_cuenta(context, nombre, slug):
    context.browser.completar('id_nombre', nombre)
    context.browser.completar('id_slug', slug)
    context.browser.pulsar()


@when('agrego una cuenta con nombre "{nombre}"')
def agregar_cuenta(context, nombre):
    context.execute_steps(
        f'Cuando agrego una cuenta con nombre "{nombre}" y slug "{nombre[:1]}"'
    )


@when('agrego una cuenta')
def agregar_cuenta(context):
    context.execute_steps('Cuando agrego una cuenta con nombre "Efectivo"')


@when('agrego un movimiento con campos')
def agregar_movimiento(context):
    for fila in context.table:
        context.browser.completar(f"id_{fila['nombre']}", fila['valor'])
    context.browser.pulsar()


@when('cliqueo en el {orden} botón de {atributo} "{texto}"')
def cliquear_en(context, orden, atributo, texto):
    if atributo == 'clase':
        atr = By.CLASS_NAME
    elif atributo == 'id':
        atr = By.ID
    else:
        atr = By.LINK_TEXT
    context.browser.esperar_elementos(texto, atr)[ORDINALES[orden]].click()


@when('cliqueo en el botón de {atributo} "{texto}"')
def cliquear_en(context, atributo, texto):
    context.execute_steps(
        f'Cuando cliqueo en el primer botón de {atributo} "{texto}"'
    )


@when('cliqueo en el botón')
def cliquear_en(context):
    context.execute_steps(
        'Cuando cliqueo en el botón de id "id_btn_submit"'
    )


@when('cliqueo en el botón "{texto}"')
def cliquear_en_el_boton(context, texto):
    context.execute_steps(
        f'Cuando cliqueo en el botón de contenido "{texto}"'
    )


@when('completo el form de dividir cuenta con estos valores')
def completar_form_dividir_cuenta(context):
    for ind, fila in enumerate(context.table):
        context.browser.completar(f'id_form-{ind}-nombre', fila['nombre'])
        context.browser.completar(f'id_form-{ind}-slug', fila['slug'])
        context.browser.completar(f'id_form-{ind}-saldo', fila['saldo'])
    context.browser.pulsar()


@when('entro en la cuenta "{nombre}"')
def entrar_en_cuenta(context, nombre):
    slug = Cuenta.tomar(nombre=nombre).slug
    context.browser.esperar_elemento(nombre, By.LINK_TEXT).click()
    context.test.assertEqual(
        context.browser.esperar_elemento(
            f'#id_div_cta_{slug} .class_nombre_cuenta_main',
            By.CSS_SELECTOR
        ).text,
        nombre
    )


@when('escribo "{texto}" en el campo "{campo}"')
def completar_campo(context, texto, campo):
    context.browser.completar(f'input[name="{campo}"]', texto, By.CSS_SELECTOR)


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


@then('el saldo general es la suma de los de "{cta1}" y "{cta2}"')
def saldo_general_es(context, cta1, cta2):
    cta1 = Cuenta.tomar(nombre=cta1)
    cta2 = Cuenta.tomar(nombre=cta2)
    context.test.assertEqual(
        context.browser.esperar_elemento('id_importe_saldo_gral').text,
        f'{cta1.saldo + cta2.saldo:.2f}'
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


@then('no veo una cuenta {nombre} en la grilla')
def cuenta_no_esta_en_grilla(context, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertNotIn(
        nombre,
        [x.find_element_by_class_name('class_nombre_cuenta').text
         for x in cuentas]
    )


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
        f'La página {cuenta} muestra {num_subcuentas} subcuentas, no {x}.'
    )


@then('veo las subcuentas de "{nombre_cta}"')
def detalle_muestra_subcuentas_de(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta)
    subctas_pag = [x.text for x in context.browser.esperar_elementos(
        'link_cuenta'
    )]
    context.test.assertEqual(
        subctas_pag,
        [x.nombre for x in cta.subcuentas.all()]
    )


@then('veo que el saldo {nombre} es {tantos} pesos')
def el_saldo_general_es_tanto(context, nombre, tantos):
    if nombre == 'general':
        total = context.browser.esperar_elemento('id_importe_saldo_gral')
    else:
        nombre = nombre[3:]
        if nombre[0] == '"':
            nombre = nombre[1:-1]
        slug = Cuenta.tomar(nombre=nombre).slug
        total = context.browser.esperar_elemento(f'id_saldo_cta_{slug}')

    if tantos == 'cero':
        tantos = '0.00'
    elif tantos.find('.') == -1:
        tantos += '.00'

    context.test.assertEqual(
        total.text, tantos
    )


@then('veo que el nombre de la cuenta es "{nombre}"')
def el_nombre_es_tal(context, nombre):
    nombre_en_pag = context.browser.esperar_elemento(
        'class_nombre_cuenta', By.CLASS_NAME).text
    context.test.assertEqual(nombre_en_pag, nombre)


@then('veo {num} movimient{os} en la página')
def veo_movimiento(context, num, os):
    if num == 'un':
        num = 1
    else:
        num = int(num)

    lista_ult_movs = context.browser.esperar_elemento('id_lista_ult_movs')
    ult_movs = lista_ult_movs.find_elements_by_tag_name('tr')

    context.test.assertEqual(len(ult_movs), num+1)  # El encabezado y un movimiento


@then('veo sólo los movimientos relacionados con "{nombre_cta}" o con sus subcuentas')
def veo_solo_movimientos_relacionados_con_cta_o_subctas(context, nombre_cta):
    cta = Cuenta.tomar(nombre=nombre_cta)
    movs_pag = [x.text for x in context.browser.esperar_elementos(
        '.class_row_mov td.class_td_concepto',
        By.CSS_SELECTOR
    )]
    context.test.assertEqual(movs_pag, [x.concepto for x in cta.movs()])


@then('veo sólo los movimientos relacionados con "{nombre_cta}"')
def veo_solo_movimientos_relacionados_con(context, nombre_cta):
    context.execute_steps(
        f'Entonces veo sólo los movimientos relacionados con "{nombre_cta}" '
        f'o con sus subcuentas'
    )


@then('veo una cuenta en la grilla con nombre "{nombre}"')
def veo_una_cuenta(context, nombre):
    cuentas = context.browser.esperar_elementos('class_div_cuenta')
    context.test.assertIn(
        nombre,
        [x.find_element_by_class_name('class_nombre_cuenta').text
         for x in cuentas]
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
